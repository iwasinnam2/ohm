"""Extract token usage from OpenAI-compatible SSE lines for stream metering."""

from __future__ import annotations

import json
from typing import Any, Optional


def usage_total_from_dict(usage: dict[str, Any] | None) -> Optional[int]:
    if not usage:
        return None
    if "total_tokens" in usage and usage["total_tokens"] is not None:
        return max(0, int(usage["total_tokens"]))
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if prompt is None and completion is None:
        # Anthropic-shaped (already mapped or raw)
        inp = usage.get("input_tokens")
        out = usage.get("output_tokens")
        if inp is None and out is None:
            return None
        return max(0, int(inp or 0) + int(out or 0))
    return max(0, int(prompt or 0) + int(completion or 0))


def usage_from_sse_line(line: str) -> Optional[int]:
    """
    Parse a single SSE line (with or without leading 'data: ') for a usage object.
    OpenAI emits a final chunk with choices=[] and usage when stream_options.include_usage.
    """
    text = line.strip()
    if not text or text == "data: [DONE]" or text == "[DONE]":
        return None
    if text.startswith("data:"):
        text = text[5:].strip()
    if not text or text == "[DONE]":
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return usage_total_from_dict(payload.get("usage"))


def approx_tokens_from_sse_lines(lines: list[str]) -> int:
    """Last-resort estimate when upstream never returned usage."""
    return max(1, sum(len(x) for x in lines) // 4)
