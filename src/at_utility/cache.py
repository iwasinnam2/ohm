"""Exact-match prompt hashing and cache helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def cache_key_for_request(
    *,
    tenant: str,
    model: str,
    messages: list[dict[str, Any]],
    extras: dict[str, Any] | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "extras": extras or {},
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"at:{tenant}:cache:{digest}"
