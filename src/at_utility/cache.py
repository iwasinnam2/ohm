"""Exact-match prompt hashing and cache helpers.

Key namespace v2: message content is normalized before hashing — CRLF/CR to
LF and outer whitespace stripped per message. Interior whitespace is never
touched (code blocks stay significant), and nothing semantic is guessed at:
exact-match remains the correctness guarantee; v2 only removes transport
noise that made byte-identical prompts miss.

The Rust edge (gateway-rs cache_key_structured) mirrors this normalization
and namespace byte-for-byte — change one side only and edge HITs silently
vanish. Parity is pinned by tests/test_units.py::test_cache_key_v2_parity
and the gateway-rs cache_key tests.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


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


def cache_key_for_request(
    *,
    tenant: str,
    model: str,
    messages: list[dict[str, Any]],
    extras: dict[str, Any] | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": _normalized_messages(messages),
        "extras": extras or {},
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"at:{tenant}:cache:v2:{digest}"
