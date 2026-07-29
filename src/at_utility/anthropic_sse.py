"""Translate Anthropic Messages SSE events into OpenAI chat.completion.chunk frames."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional


def _chunk(
    *,
    chunk_id: str,
    model: str,
    created: int,
    delta: dict[str, Any],
    finish_reason: Optional[str] = None,
    usage: Optional[dict[str, int]] = None,
) -> str:
    payload: dict[str, Any] = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
    if usage is not None:
        payload["usage"] = usage
        # Match OpenAI include_usage final frame shape
        if not delta and finish_reason is None:
            payload["choices"] = []
    return f"data: {json.dumps(payload)}\n\n"


def anthropic_usage_to_openai(
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> dict[str, int]:
    return {
        "prompt_tokens": max(0, input_tokens),
        "completion_tokens": max(0, output_tokens),
        "total_tokens": max(0, input_tokens) + max(0, output_tokens),
    }


class AnthropicToOpenAIStreamTranslator:
    """Stateful mapper: Anthropic event JSON → zero or more OpenAI SSE data lines."""

    def __init__(self, model: str):
        self.model = model
        self.chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        self.created = int(time.time())
        self.input_tokens = 0
        self.output_tokens = 0
        self._role_sent = False
        self._stopped = False
        self._finish_reason = "stop"

    def feed_event(self, event_type: str | None, data: dict[str, Any]) -> list[str]:
        et = event_type or data.get("type") or ""
        out: list[str] = []

        if et == "message_start":
            message = data.get("message") or {}
            usage = message.get("usage") or {}
            self.input_tokens = int(usage.get("input_tokens") or 0)
            if not self._role_sent:
                self._role_sent = True
                out.append(
                    _chunk(
                        chunk_id=self.chunk_id,
                        model=self.model,
                        created=self.created,
                        delta={"role": "assistant", "content": ""},
                    )
                )
            return out

        if et == "content_block_delta":
            delta = data.get("delta") or {}
            if delta.get("type") == "text_delta":
                text = delta.get("text") or ""
                if text:
                    if not self._role_sent:
                        self._role_sent = True
                        out.append(
                            _chunk(
                                chunk_id=self.chunk_id,
                                model=self.model,
                                created=self.created,
                                delta={"role": "assistant", "content": ""},
                            )
                        )
                    out.append(
                        _chunk(
                            chunk_id=self.chunk_id,
                            model=self.model,
                            created=self.created,
                            delta={"content": text},
                        )
                    )
            return out

        if et == "message_delta":
            usage = data.get("usage") or {}
            if "output_tokens" in usage:
                self.output_tokens = int(usage.get("output_tokens") or 0)
            stop = (data.get("delta") or {}).get("stop_reason")
            # Anthropic end_turn → OpenAI stop; keep others as strings when present
            if stop == "end_turn":
                self._finish_reason = "stop"
            elif stop:
                self._finish_reason = str(stop)
            return out

        if et == "message_stop":
            if self._stopped:
                return out
            self._stopped = True
            finish = self._finish_reason
            out.append(
                _chunk(
                    chunk_id=self.chunk_id,
                    model=self.model,
                    created=self.created,
                    delta={},
                    finish_reason=finish,
                )
            )
            usage = anthropic_usage_to_openai(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
            )
            out.append(
                _chunk(
                    chunk_id=self.chunk_id,
                    model=self.model,
                    created=self.created,
                    delta={},
                    finish_reason=None,
                    usage=usage,
                )
            )
            out.append("data: [DONE]\n\n")
            return out

        return out


def parse_anthropic_sse_block(block: str) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Parse one Anthropic SSE event block (may contain event: + data: lines)."""
    event_type: Optional[str] = None
    data_lines: list[str] = []
    for raw in block.splitlines():
        line = raw.strip("\r")
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return event_type, None
    try:
        payload = json.loads("\n".join(data_lines))
    except json.JSONDecodeError:
        return event_type, None
    if isinstance(payload, dict):
        return event_type or payload.get("type"), payload
    return event_type, None
