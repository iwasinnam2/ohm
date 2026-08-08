"""Swappable model backends (OrderGateway Protocol pattern from forex fsm.py)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator, Optional, Protocol

import httpx

from at_utility.anthropic_sse import (
    AnthropicToOpenAIStreamTranslator,
    anthropic_usage_to_openai,
    parse_anthropic_sse_block,
)


class ProviderUpstreamError(Exception):
    """Upstream LLM provider returned a non-success HTTP status."""

    def __init__(self, provider: str, status_code: int, body: Any):
        self.provider = provider
        self.status_code = status_code
        self.body = body
        super().__init__(f"{provider} upstream {status_code}")


class ModelProvider(Protocol):
    name: str

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """Return a full OpenAI-shaped response dict, or SSE data lines if stream=True."""
        ...


def _openai_response(
    model: str,
    content: str,
    *,
    usage: Optional[dict[str, int]] = None,
) -> dict[str, Any]:
    if usage is None:
        usage = {
            "prompt_tokens": max(1, len(content) // 8),
            "completion_tokens": max(1, len(content) // 4),
            "total_tokens": max(2, len(content) // 4 + len(content) // 8),
        }
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": usage,
    }


class MockProvider:
    name = "mock"

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[str]:
        last = messages[-1]["content"] if messages else ""
        content = f"[mock:{model}] {last}"
        if not stream:
            return _openai_response(model or "mock", content)

        async def gen() -> AsyncIterator[str]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created = int(time.time())
            for token in content.split(" "):
                payload = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model or "mock",
                    "choices": [
                        {"index": 0, "delta": {"content": token + " "}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(payload)}\n\n"
            done = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model or "mock",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(done)}\n\n"
            # Emit usage so stream metering can bill without //4 fallback
            prompt_tokens = max(1, len(str(last)) // 8)
            completion_tokens = max(1, len(content) // 4)
            usage_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model or "mock",
                "choices": [],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
            yield f"data: {json.dumps(usage_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return gen()


class OpenAIProvider:
    """OpenAI-compatible /chat/completions backend (OpenAI or any compat vendor)."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        client: Optional[httpx.AsyncClient] = None,
        name: str = "openai",
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=120.0)
        self.name = name

    def with_api_key(self, api_key: str) -> "OpenAIProvider":
        """BYOK: reuse HTTP client + base URL with a customer upstream key."""
        return OpenAIProvider(api_key, self._base_url, client=self._client, name=self.name)

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[str]:
        body = {"model": model, "messages": messages, "stream": stream, **kwargs}
        if stream:
            # Prefer provider usage in the final SSE chunk for accurate metering
            opts = body.get("stream_options")
            if isinstance(opts, dict):
                body["stream_options"] = {**opts, "include_usage": True}
            else:
                body["stream_options"] = {"include_usage": True}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"
        if not stream:
            res = await self._client.post(url, headers=headers, json=body)
            if res.status_code >= 400:
                try:
                    err_body: Any = res.json()
                except Exception:  # noqa: BLE001
                    err_body = {"error": {"message": res.text}}
                raise ProviderUpstreamError(self.name, res.status_code, err_body)
            return res.json()

        async def gen() -> AsyncIterator[str]:
            async with self._client.stream("POST", url, headers=headers, json=body) as res:
                if res.status_code >= 400:
                    text = await res.aread()
                    try:
                        err_body = json.loads(text.decode("utf-8"))
                    except Exception:  # noqa: BLE001
                        err_body = {"error": {"message": text.decode("utf-8", errors="replace")}}
                    raise ProviderUpstreamError(self.name, res.status_code, err_body)
                async for line in res.aiter_lines():
                    if line:
                        yield line + "\n"
                    if line == "data: [DONE]":
                        yield "\n"

        return gen()


class AnthropicProvider:
    """Anthropic Messages → OpenAI-shaped adapter (including true SSE translation)."""

    name = "anthropic"
    _url = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, client: Optional[httpx.AsyncClient] = None):
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=120.0)

    def with_api_key(self, api_key: str) -> "AnthropicProvider":
        """BYOK: reuse HTTP client with a customer upstream key."""
        return AnthropicProvider(api_key, client=self._client)

    def _build_body(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        # `system` may be a content-block list carrying its own `cache_control`
        # breakpoint (see docs prompt-caching "Structuring your prompt").
        # Forcing it to str() here used to silently corrupt that breakpoint —
        # forward block arrays verbatim instead, and only flatten plain
        # strings the way we always have.
        #
        # Multiple system messages are unusual but must not silently drop
        # content: if any of them carries block content, every system
        # message is merged into one ordered block list (plain strings are
        # wrapped as `{"type": "text", "text": ...}`); otherwise plain
        # strings are joined as before.
        system_blocks: list[Any] = []
        system_parts: list[str] = []
        has_block_content = False
        converted: list[dict[str, Any]] = []
        for m in messages:
            if m.get("role") == "system":
                content = m.get("content")
                if isinstance(content, list):
                    has_block_content = True
                    system_blocks.extend(content)
                elif content:
                    text = str(content)
                    system_parts.append(text)
                    system_blocks.append({"type": "text", "text": text})
            else:
                converted.append({"role": m["role"], "content": m["content"]})
        system: Any = None
        if has_block_content:
            system = system_blocks
        elif system_parts:
            system = "\n\n".join(system_parts)
        body: dict[str, Any] = {
            "model": model,
            "messages": converted,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "stream": stream,
        }
        if system:
            body["system"] = system
        # Tool definitions (and their own per-tool cache_control breakpoints)
        # were previously unrepresentable — ChatCompletionRequest had no
        # `tools` field at all, so they were dropped before ever reaching here.
        tools = kwargs.get("tools")
        if tools:
            body["tools"] = tools
        tool_choice = kwargs.get("tool_choice")
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        return body

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[str]:
        body = self._build_body(model=model, messages=messages, stream=stream, kwargs=kwargs)
        headers = self._headers()

        if stream:
            return self._stream_openai_sse(model=model, body=body, headers=headers)

        res = await self._client.post(self._url, headers=headers, json=body)
        if res.status_code >= 400:
            try:
                err_body: Any = res.json()
            except Exception:  # noqa: BLE001
                err_body = {"error": {"message": res.text}}
            raise ProviderUpstreamError(self.name, res.status_code, err_body)
        data = res.json()
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        raw_usage = data.get("usage") or {}
        usage = anthropic_usage_to_openai(
            input_tokens=int(raw_usage.get("input_tokens") or 0),
            output_tokens=int(raw_usage.get("output_tokens") or 0),
            cache_creation_input_tokens=int(
                raw_usage.get("cache_creation_input_tokens") or 0
            ),
            cache_read_input_tokens=int(raw_usage.get("cache_read_input_tokens") or 0),
        )
        if usage["total_tokens"] == 0:
            return _openai_response(model, text)
        return _openai_response(model, text, usage=usage)

    def _stream_openai_sse(
        self,
        *,
        model: str,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> AsyncIterator[str]:
        client = self._client
        url = self._url
        provider = self.name

        async def gen() -> AsyncIterator[str]:
            translator = AnthropicToOpenAIStreamTranslator(model)
            async with client.stream("POST", url, headers=headers, json=body) as res:
                if res.status_code >= 400:
                    text = await res.aread()
                    try:
                        err_body = json.loads(text.decode("utf-8"))
                    except Exception:  # noqa: BLE001
                        err_body = {"error": {"message": text.decode("utf-8", errors="replace")}}
                    raise ProviderUpstreamError(provider, res.status_code, err_body)

                buf = ""
                async for chunk in res.aiter_text():
                    buf += chunk
                    while "\n\n" in buf:
                        block, buf = buf.split("\n\n", 1)
                        if not block.strip():
                            continue
                        event_type, data = parse_anthropic_sse_block(block)
                        if data is None:
                            continue
                        for line in translator.feed_event(event_type, data):
                            yield line

                # Flush trailing block without trailing blank line
                if buf.strip():
                    event_type, data = parse_anthropic_sse_block(buf)
                    if data is not None:
                        for line in translator.feed_event(event_type, data):
                            yield line

                if not translator._stopped:
                    for line in translator.feed_event("message_stop", {"type": "message_stop"}):
                        yield line

        return gen()


# OpenAI-compatible vendor registry: (vendor, model prefixes, default base URL).
# One X-Ohm-Upstream-Key BYOK header routes to whichever vendor the prefix
# resolves to; env keys ({VENDOR}_API_KEY) are dev fallback / managed pool only.
OPENAI_COMPAT_VENDORS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("gemini", ("gemini-",), "https://generativelanguage.googleapis.com/v1beta/openai"),
    ("deepseek", ("deepseek-",), "https://api.deepseek.com/v1"),
    ("moonshot", ("kimi-", "moonshot-"), "https://api.moonshot.ai/v1"),
    ("zai", ("glm-",), "https://api.z.ai/api/paas/v4"),
    ("qwen", ("qwen",), "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
    ("xai", ("grok-",), "https://api.x.ai/v1"),
)


def compat_vendor_for_model(model: str) -> Optional[str]:
    """Vendor id for an OpenAI-compatible model prefix, or None."""
    m = (model or "").lower()
    for vendor, prefixes, _base in OPENAI_COMPAT_VENDORS:
        if any(m.startswith(p) for p in prefixes):
            return vendor
    return None


def compat_default_base_url(vendor: str) -> str:
    for v, _prefixes, base in OPENAI_COMPAT_VENDORS:
        if v == vendor:
            return base
    raise KeyError(vendor)


def build_compat_shells(settings: Any) -> dict[str, OpenAIProvider]:
    """Construct per-vendor OpenAI-compatible shells (BYOK clones from these)."""
    shells: dict[str, OpenAIProvider] = {}
    for vendor, _prefixes, default_base in OPENAI_COMPAT_VENDORS:
        key = getattr(settings, f"{vendor}_api_key", "") or ""
        base = getattr(settings, f"{vendor}_base_url", "") or default_base
        shells[vendor] = OpenAIProvider(key, base, name=vendor)
    return shells


def resolve_provider(
    model: str,
    *,
    openai: Optional[OpenAIProvider],
    anthropic: Optional[AnthropicProvider],
    mock: MockProvider,
    fallback: str,
    upstream_key: str = "",
    allow_env_fallback: bool = True,
    compat: Optional[dict[str, OpenAIProvider]] = None,
) -> tuple[ModelProvider, str]:
    """
    Pick a backend. Prefer BYOK `upstream_key` for gpt/claude/compat vendors;
    else env-backed providers when allow_env_fallback; else mock for mock/auto.
    """
    m = (model or "").lower()
    key = (upstream_key or "").strip()

    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        if key:
            base = openai or OpenAIProvider(key, "https://api.openai.com/v1")
            return base.with_api_key(key) if openai else OpenAIProvider(key, base._base_url), model
        if allow_env_fallback and openai and openai._api_key:
            return openai, model
        return mock, "mock"

    if m.startswith("claude"):
        if key:
            base = anthropic or AnthropicProvider(key)
            return base.with_api_key(key) if anthropic else AnthropicProvider(key), model
        if allow_env_fallback and anthropic and anthropic._api_key:
            return anthropic, model
        return mock, "mock"

    vendor = compat_vendor_for_model(m)
    if vendor is not None:
        shell = (compat or {}).get(vendor) or OpenAIProvider(
            "", compat_default_base_url(vendor), name=vendor
        )
        if key:
            return shell.with_api_key(key), model
        if allow_env_fallback and shell._api_key:
            return shell, model
        return mock, "mock"

    if m in ("mock", "", "auto"):
        return mock, "mock"

    if key:
        base = openai or OpenAIProvider(key, "https://api.openai.com/v1")
        return base.with_api_key(key) if openai else OpenAIProvider(key, base._base_url), model
    if allow_env_fallback and openai and openai._api_key:
        return openai, model
    fb = fallback.lower()
    if (
        allow_env_fallback
        and fb.startswith("claude")
        and anthropic
        and anthropic._api_key
    ):
        return anthropic, fallback
    return mock, "mock"


def model_needs_upstream(model: str) -> bool:
    m = (model or "").lower()
    if m in ("mock", "", "auto"):
        return False
    return True


def provider_key_available(
    model: str,
    *,
    upstream_key: str,
    openai: Optional[OpenAIProvider],
    anthropic: Optional[AnthropicProvider],
    allow_env_fallback: bool,
    compat: Optional[dict[str, OpenAIProvider]] = None,
) -> bool:
    if not model_needs_upstream(model):
        return True
    if (upstream_key or "").strip():
        return True
    if not allow_env_fallback:
        return False
    m = (model or "").lower()
    if m.startswith("claude"):
        return bool(anthropic and anthropic._api_key)
    vendor = compat_vendor_for_model(m)
    if vendor is not None:
        shell = (compat or {}).get(vendor)
        return bool(shell and shell._api_key)
    return bool(openai and openai._api_key)
