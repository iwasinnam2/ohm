"""Breakpoint autopilot — auto-places Anthropic `cache_control` breakpoints.

See docs/CACHE_AUTOPILOT.md for the full design/ADR. Short version: naive
agent clients (Cursor-style) resend the *entire* growing transcript every
turn and either place no `cache_control` at all, or place it on the last
(per-turn-varying) block, which never hits. Ohm already sits in the request
path on every MISS, so it can transparently find the longest byte-stable
prefix across turns of the same logical session and place the breakpoint
correctly — without the client ever knowing prompt caching exists.

This is intentionally coarse-grained (message-level, not Anthropic's finer
content-block level) and byte-exact (sha256 equality, no embeddings/fuzzy
matching) — same philosophy as the existing exact-replay cache, just applied
one layer down instead of to the whole request.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from at_utility.redis_store import CacheStore, tenant_key

EPHEMERAL_CACHE_CONTROL = {"type": "ephemeral"}
LEDGER_KIND = "cacheledger"


def _strip_cache_control(value: Any) -> Any:
    """Deep-copy `value` with any `cache_control` keys removed, so a
    breakpoint (ours or the client's own) never itself counts as a content
    change for prefix-stability comparisons."""
    if isinstance(value, dict):
        return {k: _strip_cache_control(v) for k, v in value.items() if k != "cache_control"}
    if isinstance(value, list):
        return [_strip_cache_control(v) for v in value]
    return value


def _unit_digest(value: Any) -> str:
    cleaned = _strip_cache_control(value)
    blob = json.dumps(cleaned, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _has_cache_control(value: Any) -> bool:
    if isinstance(value, dict):
        if "cache_control" in value:
            return True
        return any(_has_cache_control(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_cache_control(v) for v in value)
    return False


@dataclass
class CacheUnit:
    """One breakpoint-eligible unit in Anthropic's cache hierarchy order
    (tools → system → messages)."""

    kind: str  # "tools" | "message"
    index: int  # index into `messages` for kind="message"; -1 for "tools"
    digest: str
    has_client_cache_control: bool


def build_cache_units(
    *, tools: Optional[list[dict[str, Any]]], messages: list[dict[str, Any]]
) -> list[CacheUnit]:
    units: list[CacheUnit] = []
    if tools:
        units.append(
            CacheUnit(
                kind="tools",
                index=-1,
                digest=_unit_digest(tools),
                has_client_cache_control=_has_cache_control(tools),
            )
        )
    for i, m in enumerate(messages):
        units.append(
            CacheUnit(
                kind="message",
                index=i,
                digest=_unit_digest(m),
                has_client_cache_control=_has_cache_control(m),
            )
        )
    return units


def resolve_session_id(
    *,
    header: Optional[str],
    body_session: Optional[str],
    tenant: str,
    model: str,
    messages: list[dict[str, Any]],
) -> str:
    """Stable identity for "this logical conversation" across turns.

    Prefers an explicit id (X-Ohm-Session header, or `ohm_session` body
    field). Falls back to a hash of the first two messages (typically the
    system prompt + first user turn) — these stay constant while a
    conversation grows, so this is a solid session anchor even without an
    explicit id. Multiple concurrent conversations sharing an identical
    opening are the known limitation of the fallback; send X-Ohm-Session to
    disambiguate.
    """
    explicit = (header or body_session or "").strip()
    if explicit:
        return explicit
    anchor: list[str] = [tenant, model]
    for m in messages[:2]:
        anchor.append(str(m.get("role") or ""))
        anchor.append(_unit_digest(m.get("content")))
    return hashlib.sha256("|".join(anchor).encode("utf-8")).hexdigest()[:32]


def _ledger_key(tenant: str, session_id: str) -> str:
    return tenant_key(tenant, LEDGER_KIND, session_id)


def _longest_common_prefix(prev: list[str], curr: list[str]) -> int:
    n = min(len(prev), len(curr))
    k = 0
    while k < n and prev[k] == curr[k]:
        k += 1
    return k


def _inject_breakpoint(
    *,
    tools: Optional[list[dict[str, Any]]],
    messages: list[dict[str, Any]],
    unit: CacheUnit,
) -> tuple[Optional[list[dict[str, Any]]], list[dict[str, Any]]]:
    """Return (tools, messages) deep-copied with `unit` carrying an ephemeral
    cache_control breakpoint. Never mutates the caller's originals."""
    if unit.kind == "tools":
        new_tools = copy.deepcopy(tools) or []
        if new_tools:
            new_tools[-1] = {**new_tools[-1], "cache_control": dict(EPHEMERAL_CACHE_CONTROL)}
        return new_tools, messages

    new_messages = copy.deepcopy(messages)
    target = new_messages[unit.index]
    content = target.get("content")
    if isinstance(content, str):
        target["content"] = [
            {"type": "text", "text": content, "cache_control": dict(EPHEMERAL_CACHE_CONTROL)}
        ]
    elif isinstance(content, list) and content:
        blocks = [dict(b) if isinstance(b, dict) else b for b in content]
        if isinstance(blocks[-1], dict):
            blocks[-1] = {**blocks[-1], "cache_control": dict(EPHEMERAL_CACHE_CONTROL)}
        target["content"] = blocks
    return tools, new_messages


@dataclass
class AutopilotResult:
    tools: Optional[list[dict[str, Any]]]
    messages: list[dict[str, Any]]
    # injected | client_managed | no_stable_prefix | disabled | unchanged
    status: str
    stable_prefix_units: int = 0


async def apply_cache_autopilot(
    *,
    store: CacheStore,
    settings: Any,
    tenant: str,
    model: str,
    session_id: str,
    tools: Optional[list[dict[str, Any]]],
    messages: list[dict[str, Any]],
) -> AutopilotResult:
    """Diff this request's cache units against the tenant/session's prefix
    ledger, and — only when useful and safe — inject one ephemeral
    `cache_control` breakpoint before the request goes to Anthropic.

    Always updates the ledger (best-effort) so the *next* turn has something
    to diff against, even when this turn doesn't inject anything.
    """
    if not getattr(settings, "at_cache_autopilot_enabled", True):
        return AutopilotResult(tools=tools, messages=messages, status="disabled")

    units = build_cache_units(tools=tools, messages=messages)
    if any(u.has_client_cache_control for u in units):
        # A cache-aware client is already managing its own breakpoints —
        # never add a second one on top (Anthropic caps at 4 total, and a
        # collision would waste a slot rather than help).
        await _write_ledger(store, settings, tenant, session_id, units, last_breakpoint=None)
        return AutopilotResult(tools=tools, messages=messages, status="client_managed")

    raw = await store.get(_ledger_key(tenant, session_id))
    prev_digests: list[str] = []
    prev_breakpoint: Optional[int] = None
    if raw:
        try:
            parsed = json.loads(raw)
            prev_digests = list(parsed.get("digests") or [])
            prev_breakpoint = parsed.get("last_breakpoint")
        except (ValueError, TypeError):
            prev_digests = []

    curr_digests = [u.digest for u in units]
    k = _longest_common_prefix(prev_digests, curr_digests)

    if k == 0:
        # Nothing stable yet (first turn, or the prefix changed entirely) —
        # nothing to gain from a breakpoint this turn. Just seed the ledger.
        await _write_ledger(store, settings, tenant, session_id, units, last_breakpoint=None)
        return AutopilotResult(tools=tools, messages=messages, status="no_stable_prefix")

    target_index = k - 1
    lookback = int(getattr(settings, "at_cache_autopilot_lookback_units", 16) or 16)
    breakpoint_still_fresh = (
        prev_breakpoint is not None
        and prev_breakpoint < k
        and (target_index - prev_breakpoint) < lookback
    )
    if breakpoint_still_fresh:
        # A still-valid breakpoint already sits inside Anthropic's lookback
        # window from here — no need to spend another one.
        await _write_ledger(
            store, settings, tenant, session_id, units, last_breakpoint=prev_breakpoint
        )
        return AutopilotResult(
            tools=tools, messages=messages, status="unchanged", stable_prefix_units=k
        )

    new_tools, new_messages = _inject_breakpoint(
        tools=tools, messages=messages, unit=units[target_index]
    )
    await _write_ledger(
        store, settings, tenant, session_id, units, last_breakpoint=target_index
    )
    return AutopilotResult(
        tools=new_tools, messages=new_messages, status="injected", stable_prefix_units=k
    )


async def _write_ledger(
    store: CacheStore,
    settings: Any,
    tenant: str,
    session_id: str,
    units: list[CacheUnit],
    *,
    last_breakpoint: Optional[int],
) -> None:
    ttl = int(getattr(settings, "at_cache_autopilot_ttl_seconds", 300) or 300)
    payload = json.dumps(
        {
            "digests": [u.digest for u in units],
            "last_breakpoint": last_breakpoint,
            "written_at": time.time(),
            "ttl_seconds": ttl,
        }
    )
    await store.set(_ledger_key(tenant, session_id), payload, ttl_seconds=ttl)


@dataclass
class SessionStatus:
    tracked: bool
    stable_prefix_units: int = 0
    last_breakpoint: Optional[int] = None
    ttl_seconds: int = 0
    ttl_remaining_seconds: float = 0.0


async def session_status(
    *, store: CacheStore, tenant: str, session_id: str
) -> SessionStatus:
    """Cheap read so a client (or its own idle timer) can decide whether a
    session is worth pre-warming — see docs/CACHE_AUTOPILOT.md Phase 3 /
    POST /v1/chat/completions/prewarm."""
    raw = await store.get(_ledger_key(tenant, session_id))
    if not raw:
        return SessionStatus(tracked=False)
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return SessionStatus(tracked=False)
    ttl = int(parsed.get("ttl_seconds") or 0)
    written_at = float(parsed.get("written_at") or 0.0)
    remaining = max(0.0, (written_at + ttl) - time.time()) if ttl and written_at else 0.0
    return SessionStatus(
        tracked=True,
        stable_prefix_units=len(parsed.get("digests") or []),
        last_breakpoint=parsed.get("last_breakpoint"),
        ttl_seconds=ttl,
        ttl_remaining_seconds=remaining,
    )
