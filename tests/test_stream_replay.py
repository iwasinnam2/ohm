"""SSE replay: streamed responses populate and are served from the same
cache entries as JSON responses. A truncated stream must never be cached."""

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from at_utility.metering import Meter
from at_utility.providers import MockProvider
from at_utility.redis_store import MemoryStore
from at_utility.stream_usage import (
    assemble_completion_from_sse_lines,
    sse_lines_from_completion,
)
from at_utility.tenants import TenantRegistry
import at_utility.main as main_mod

HEADERS = {"Authorization": "Bearer sk-at-dev"}


@pytest.fixture(autouse=True)
async def _mem_state():
    get_settings.cache_clear()
    store = MemoryStore()
    settings = get_settings()
    main_mod.state.settings = settings
    main_mod.state.store = store
    main_mod.state.meter = Meter(store, settings)
    main_mod.state.tenants = TenantRegistry(store, settings)
    main_mod.state.mock = MockProvider()
    main_mod.state.openai = None
    main_mod.state.anthropic = None
    yield
    await store.close()
    get_settings.cache_clear()


def _payload(content: str, stream: bool) -> dict:
    return {
        "model": "mock",
        "stream": stream,
        "messages": [{"role": "user", "content": content}],
    }


@pytest.mark.asyncio
async def test_stream_miss_then_stream_hit_replays():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("replay-me", True)
        )
        assert miss.status_code == 200
        assert miss.headers.get("x-at-cache") == "MISS"

        hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("replay-me", True)
        )
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache") == "HIT"
        assert "text/event-stream" in hit.headers.get("content-type", "")
        assert float(hit.headers.get("x-at-billed-usd", "0")) >= 0
        body = hit.text
        assert "data: [DONE]" in body
        assert '"usage"' in body
        assert "[mock:mock] replay-me" in body


@pytest.mark.asyncio
async def test_stream_miss_populates_json_hit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("cross-a", True)
        )
        assert miss.headers.get("x-at-cache") == "MISS"

        hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("cross-a", False)
        )
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache") == "HIT"
        content = hit.json()["choices"][0]["message"]["content"]
        assert "[mock:mock] cross-a" in content
        assert hit.json()["usage"]["total_tokens"] > 0


@pytest.mark.asyncio
async def test_json_miss_serves_stream_hit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("cross-b", False)
        )
        assert miss.headers.get("x-at-cache") == "MISS"

        hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("cross-b", True)
        )
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache") == "HIT"
        assert "text/event-stream" in hit.headers.get("content-type", "")
        assert "[mock:mock] cross-b" in hit.text
        assert "data: [DONE]" in hit.text


@pytest.mark.asyncio
async def test_stream_hit_meters_as_cache_hit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("meter-me", True)
        )
        before = (await client.get("/v1/usage", headers=HEADERS)).json()
        await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload("meter-me", True)
        )
        after = (await client.get("/v1/usage", headers=HEADERS)).json()
        assert after["cache_hit_tokens"] > before["cache_hit_tokens"]
        assert after["cache_miss_tokens"] == before["cache_miss_tokens"]


def test_truncated_stream_is_never_assembled():
    # No finish_reason chunk → not a completed stream → no cache entry.
    lines = [
        'data: {"id":"x","object":"chat.completion.chunk","model":"m",'
        '"choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}\n\n',
        'data: {"id":"x","object":"chat.completion.chunk","model":"m",'
        '"choices":[{"index":0,"delta":{"content":"partial"},"finish_reason":null}]}\n\n',
    ]
    assert assemble_completion_from_sse_lines(lines) is None


def test_assemble_and_synthesize_round_trip():
    completion = {
        "id": "chatcmpl-rt",
        "object": "chat.completion",
        "created": 123,
        "model": "mock",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "hello world"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }
    lines = sse_lines_from_completion(completion)
    assert lines[-1] == "data: [DONE]\n\n"
    rebuilt = assemble_completion_from_sse_lines(lines)
    assert rebuilt is not None
    assert rebuilt["choices"][0]["message"]["content"] == "hello world"
    assert rebuilt["choices"][0]["finish_reason"] == "stop"
    assert rebuilt["usage"]["total_tokens"] == 5
