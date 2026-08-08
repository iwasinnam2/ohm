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


def usage_dict_from_sse_line(line: str) -> Optional[dict[str, Any]]:
    """Like usage_from_sse_line, but returns the full usage object instead of
    just the token total — so callers can read cache_read_input_tokens /
    cache_creation_input_tokens (Anthropic) when the upstream reports them.
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
    usage = payload.get("usage")
    return usage if isinstance(usage, dict) else None


def approx_tokens_from_sse_lines(lines: list[str]) -> int:
    """Last-resort estimate when upstream never returned usage."""
    return max(1, sum(len(x) for x in lines) // 4)


def _data_payload(line: str) -> Optional[dict[str, Any]]:
    text = line.strip()
    if not text or text in ("data: [DONE]", "[DONE]"):
        return None
    if text.startswith("data:"):
        text = text[5:].strip()
    if not text or text == "[DONE]":
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def assemble_completion_from_sse_lines(lines: list[str]) -> Optional[dict[str, Any]]:
    """
    Rebuild a full chat.completion object from collected OpenAI-shaped SSE
    chunks so a streamed MISS can populate the same cache entry the
    non-stream path uses. Returns None unless the stream terminated with a
    finish_reason — a truncated stream must never become a cache entry.
    """
    completion_id = ""
    model = ""
    created = 0
    role = "assistant"
    parts: list[str] = []
    finish_reason: Optional[str] = None
    usage: Optional[dict[str, Any]] = None

    for line in lines:
        payload = _data_payload(line)
        if payload is None:
            continue
        completion_id = completion_id or str(payload.get("id") or "")
        model = model or str(payload.get("model") or "")
        created = created or int(payload.get("created") or 0)
        if isinstance(payload.get("usage"), dict):
            usage = payload["usage"]
        for choice in payload.get("choices") or []:
            if not isinstance(choice, dict) or int(choice.get("index") or 0) != 0:
                continue
            delta = choice.get("delta") or {}
            if isinstance(delta, dict):
                if delta.get("role"):
                    role = str(delta["role"])
                piece = delta.get("content")
                if isinstance(piece, str):
                    parts.append(piece)
            if choice.get("finish_reason"):
                finish_reason = str(choice["finish_reason"])

    if finish_reason is None:
        return None
    content = "".join(parts)
    total = usage_total_from_dict(usage)
    if total is None:
        total = approx_tokens_from_sse_lines(lines)
        usage = {"prompt_tokens": 0, "completion_tokens": total, "total_tokens": total}
    return {
        "id": completion_id or "chatcmpl-replay",
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": role, "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": usage,
    }


def sse_lines_from_completion(payload: dict[str, Any]) -> list[str]:
    """
    Synthesize an OpenAI-shaped SSE replay from a cached chat.completion —
    role chunk, content chunk, finish chunk, usage chunk, [DONE] — so a
    streamed request can be served from the same cache entry as a JSON one.
    """
    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    base = {
        "id": str(payload.get("id") or "chatcmpl-replay"),
        "object": "chat.completion.chunk",
        "created": int(payload.get("created") or 0),
        "model": str(payload.get("model") or ""),
    }

    def chunk(delta: dict[str, Any], finish: Optional[str] = None) -> str:
        body = {
            **base,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
        }
        return f"data: {json.dumps(body)}\n\n"

    lines = [chunk({"role": str(message.get("role") or "assistant")})]
    content = message.get("content")
    if isinstance(content, str) and content:
        lines.append(chunk({"content": content}))
    lines.append(chunk({}, finish=str(choice.get("finish_reason") or "stop")))
    if isinstance(payload.get("usage"), dict):
        lines.append(
            "data: "
            + json.dumps({**base, "choices": [], "usage": payload["usage"]})
            + "\n\n"
        )
    lines.append("data: [DONE]\n\n")
    return lines
