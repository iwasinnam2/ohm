"""Exact-match prompt hashing and cache helpers.

Key namespace v2 (default tree ``main``): ``at:{tenant}:cache:v2:{digest}``.
Named cache trees (Phase 0+): ``at:{tenant}:tree:{tree_id}:cache:v3:{digest}``.

Message content is normalized before hashing — CRLF/CR to LF and outer
whitespace stripped per message. Interior whitespace is never touched.
Exact-match remains the correctness guarantee.

The Rust edge (gateway-rs ``cache_key_structured``) mirrors normalization and
key layout byte-for-byte — change one side only and edge HITs silently vanish.
Parity: ``tests/test_units.py`` and gateway-rs cache_key tests.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

DEFAULT_CACHE_TREE = "main"
_TREE_RE = re.compile(r"^[a-z0-9_-]{1,64}$")


def normalize_content(text: str) -> str:
    """CRLF/CR -> LF, then strip leading/trailing whitespace."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _normalized_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            normalized = normalize_content(content)
            if normalized != content:
                msg = {**msg, "content": normalized}
        out.append(msg)
    return out


def resolve_cache_tree(*, header: str | None = None, body: str | None = None) -> str:
    """Resolve cache tree id. Header wins over body. Empty → ``main``.

    Explicit non-empty values that fail ``[a-z0-9_-]{1,64}`` raise ``ValueError``.
    """
    raw = header if (header is not None and str(header).strip() != "") else body
    if raw is None or str(raw).strip() == "":
        return DEFAULT_CACHE_TREE
    s = str(raw).strip().lower()
    if not _TREE_RE.match(s):
        raise ValueError("invalid_cache_tree")
    return s


def request_digest(
    *,
    model: str,
    messages: list[dict[str, Any]],
    extras: dict[str, Any] | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": _normalized_messages(messages),
        "extras": extras or {},
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def cache_key_for_request(
    *,
    tenant: str,
    model: str,
    messages: list[dict[str, Any]],
    extras: dict[str, Any] | None = None,
    tree_id: str | None = None,
) -> str:
    """Build Redis cache key.

    Default tree ``main`` keeps the v2 key layout (HIT parity with existing
    clients). Named trees use v3 with the tree segment before the digest.
    """
    digest = request_digest(model=model, messages=messages, extras=extras)
    tree = (tree_id or DEFAULT_CACHE_TREE).strip().lower() or DEFAULT_CACHE_TREE
    if tree != DEFAULT_CACHE_TREE and not _TREE_RE.match(tree):
        raise ValueError("invalid_cache_tree")
    if tree == DEFAULT_CACHE_TREE:
        return f"at:{tenant}:cache:v2:{digest}"
    return f"at:{tenant}:tree:{tree}:cache:v3:{digest}"
