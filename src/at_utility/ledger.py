"""Corporate clean ledger — immutable append-only usage events."""

from __future__ import annotations

import csv
import io
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Optional

from at_utility.config import Settings
from at_utility.redis_store import CacheStore
from at_utility.savings import provider_avoided_usd

_PATH_RE = re.compile(r"^[a-z0-9_-]{1,64}$")


def normalize_path(raw: str | None) -> str:
    """Frequency-farm path label — lowercase [a-z0-9_-]{1,64} or default."""
    s = (raw or "").strip().lower()
    if not s or not _PATH_RE.match(s):
        return "default"
    return s


@dataclass
class LedgerEvent:
    event_id: str
    ts: int
    tenant_id: str
    org_id: str
    cost_center: str
    kind: str  # cache_hit | cache_miss | fetch
    model: str
    tokens: int
    fetches: int
    pipe_usd: float
    estimated_provider_usd: float
    cache_hit: bool
    purpose: str
    request_id: str
    path: str = "default"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "LedgerEvent":
        data = json.loads(raw)
        if "path" not in data:
            data["path"] = "default"
        return LedgerEvent(
            **{k: data[k] for k in LedgerEvent.__dataclass_fields__ if k in data}
        )


def _empty_bucket() -> dict[str, float]:
    return {
        "pipe_usd": 0.0,
        "estimated_provider_usd": 0.0,
        "events": 0.0,
        "tokens": 0.0,
        "cache_hits": 0.0,
        "cache_misses": 0.0,
        "fetches": 0.0,
    }


class CleanLedger:
    """Append-only event log keyed by org (fallback: tenant)."""

    MAX_EVENTS = 50_000

    def __init__(self, store: CacheStore, settings: Settings):
        self._store = store
        self._settings = settings

    def _list_key(self, org_id: str, tenant_id: str) -> str:
        scope = org_id if org_id else tenant_id
        return f"at:ledger:{scope}:events"

    async def append(
        self,
        *,
        tenant_id: str,
        org_id: str = "",
        cost_center: str = "default",
        kind: str,
        model: str = "",
        tokens: int = 0,
        fetches: int = 0,
        pipe_usd: float = 0.0,
        cache_hit: bool = False,
        purpose: str = "",
        request_id: str = "",
        path: str = "default",
    ) -> LedgerEvent:
        est_provider = 0.0
        if cache_hit and tokens > 0:
            est_provider = provider_avoided_usd(float(tokens), self._settings)
        ev = LedgerEvent(
            event_id=uuid.uuid4().hex,
            ts=int(time.time()),
            tenant_id=tenant_id,
            org_id=org_id or "",
            cost_center=(cost_center or "default").strip() or "default",
            kind=kind,
            model=model or "",
            tokens=int(tokens or 0),
            fetches=int(fetches or 0),
            pipe_usd=float(pipe_usd or 0),
            estimated_provider_usd=float(est_provider),
            cache_hit=bool(cache_hit),
            purpose=purpose or "",
            request_id=request_id or "",
            path=normalize_path(path),
        )
        key = self._list_key(org_id, tenant_id)
        await self._store.list_push(key, ev.to_json())
        length = await self._store.list_len(key)
        if length > self.MAX_EVENTS and hasattr(self._store, "list_trim"):
            await self._store.list_trim(key, length - self.MAX_EVENTS, -1)
        return ev

    async def list_events(
        self,
        *,
        org_id: str = "",
        tenant_id: str = "",
        cost_center: str = "",
        path: str = "",
        limit: int = 500,
        since_ts: int = 0,
        until_ts: int = 0,
    ) -> list[LedgerEvent]:
        key = self._list_key(org_id, tenant_id)
        raw_items = await self._store.list_range(key, -max(limit * 4, 500), -1)
        out: list[LedgerEvent] = []
        path_f = normalize_path(path) if path else ""
        for raw in reversed(raw_items):
            try:
                ev = LedgerEvent.from_json(raw)
            except (ValueError, TypeError, KeyError):
                continue
            if since_ts and ev.ts < since_ts:
                continue
            if until_ts and ev.ts >= until_ts:
                continue
            if cost_center and ev.cost_center != cost_center:
                continue
            if path_f and ev.path != path_f:
                continue
            out.append(ev)
            if len(out) >= limit:
                break
        return out

    async def summarize(
        self,
        *,
        org_id: str = "",
        tenant_id: str = "",
        cost_center: str = "",
        path: str = "",
        since_ts: int = 0,
        until_ts: int = 0,
    ) -> dict[str, Any]:
        events = await self.list_events(
            org_id=org_id,
            tenant_id=tenant_id,
            cost_center=cost_center,
            path=path,
            limit=10_000,
            since_ts=since_ts,
            until_ts=until_ts,
        )
        by_center: dict[str, dict[str, float]] = {}
        by_path: dict[str, dict[str, float]] = {}
        pipe = 0.0
        provider = 0.0
        hits = 0
        misses = 0
        fetches = 0
        for ev in events:
            pipe += ev.pipe_usd
            provider += ev.estimated_provider_usd
            if ev.kind == "cache_hit":
                hits += 1
            elif ev.kind == "cache_miss":
                misses += 1
            elif ev.kind == "fetch":
                fetches += ev.fetches
            for key, store in (
                (ev.cost_center, by_center),
                (ev.path or "default", by_path),
            ):
                bucket = store.setdefault(key, _empty_bucket())
                bucket["pipe_usd"] += ev.pipe_usd
                bucket["estimated_provider_usd"] += ev.estimated_provider_usd
                bucket["events"] += 1
                bucket["tokens"] += ev.tokens
                if ev.kind == "cache_hit":
                    bucket["cache_hits"] += 1
                elif ev.kind == "cache_miss":
                    bucket["cache_misses"] += 1
                elif ev.kind == "fetch":
                    bucket["fetches"] += ev.fetches
        chat_n = hits + misses
        return {
            "event_count": len(events),
            "pipe_rent_usd": round(pipe, 6),
            "estimated_provider_avoided_usd": round(provider, 6),
            "cache_hits": hits,
            "cache_misses": misses,
            "fetches": fetches,
            "hit_ratio": round(hits / chat_n, 6) if chat_n else None,
            "by_cost_center": by_center,
            "by_path": by_path,
            "estimate_only": True,
            "reconcile": {
                "pipe_rent_usd": round(pipe, 6),
                "estimated_provider_avoided_usd": round(provider, 6),
                "provider_invoice_import_usd": None,
                "note": (
                    "Provider invoice import not yet wired; provider figure is "
                    "blended list estimate on cache hits only."
                ),
            },
        }

    def hit_ratio_report(
        self,
        summary: dict[str, Any],
        *,
        group_by: str = "cost_center",
    ) -> dict[str, Any]:
        """Slice summarize() into a hit-ratio view by cost_center or path."""
        key = "by_cost_center" if group_by == "cost_center" else "by_path"
        raw = summary.get(key) or {}
        groups: dict[str, Any] = {}
        for name, bucket in raw.items():
            h = int(bucket.get("cache_hits") or 0)
            m = int(bucket.get("cache_misses") or 0)
            n = h + m
            groups[name] = {
                "cache_hits": h,
                "cache_misses": m,
                "hit_ratio": round(h / n, 6) if n else None,
                "pipe_rent_usd": round(float(bucket.get("pipe_usd") or 0), 6),
                "estimated_provider_avoided_usd": round(
                    float(bucket.get("estimated_provider_usd") or 0), 6
                ),
                "fetches": int(bucket.get("fetches") or 0),
                "events": int(bucket.get("events") or 0),
            }
        return {
            "group_by": "cost_center" if group_by == "cost_center" else "path",
            "hit_ratio": summary.get("hit_ratio"),
            "cache_hits": summary.get("cache_hits", 0),
            "cache_misses": summary.get("cache_misses", 0),
            "pipe_rent_usd": summary.get("pipe_rent_usd", 0),
            "estimated_provider_avoided_usd": summary.get(
                "estimated_provider_avoided_usd", 0
            ),
            "groups": groups,
            "estimate_only": True,
        }

    def export_csv(self, events: list[LedgerEvent]) -> str:
        buf = io.StringIO()
        w = csv.DictWriter(
            buf,
            fieldnames=[
                "event_id",
                "ts",
                "tenant_id",
                "org_id",
                "cost_center",
                "path",
                "kind",
                "model",
                "tokens",
                "fetches",
                "pipe_usd",
                "estimated_provider_usd",
                "cache_hit",
                "purpose",
                "request_id",
            ],
        )
        w.writeheader()
        for ev in events:
            w.writerow(asdict(ev))
        return buf.getvalue()

    def export_json(self, events: list[LedgerEvent]) -> list[dict[str, Any]]:
        return [asdict(ev) for ev in events]
