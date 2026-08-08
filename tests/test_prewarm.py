"""Session-aware pre-warm (docs/CACHE_AUTOPILOT.md Phase 3)."""

import json

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
import at_utility.main as main_mod
from at_utility.providers import AnthropicProvider
from tests.app_state import wire_memory_app_state


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()
    get_settings.cache_clear()


def _anthropic_transport(captured: list[dict]):
    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content.decode()))
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "ok"}],
                "usage": {
                    "input_tokens": 3,
                    "output_tokens": 1,
                    "cache_read_input_tokens": 900,
                },
            },
        )

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_session_status_untracked_for_unknown_session():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/cache/sessions/never-seen", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["tracked"] is False


@pytest.mark.asyncio
async def test_session_status_tracked_after_a_claude_turn():
    captured: list[dict] = []
    main_mod.state.anthropic = AnthropicProvider(
        "sk-ant-env", client=httpx.AsyncClient(transport=_anthropic_transport(captured))
    )
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Upstream-Key": "sk-ant-byok",
        "X-Ohm-Session": "conv-status-1",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={
                "model": "claude-3-5-sonnet-latest",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
        res = await client.get(
            "/v1/cache/sessions/conv-status-1", headers={"Authorization": "Bearer sk-at-dev"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["tracked"] is True
        assert body["stable_prefix_units"] == 1
        assert body["ttl_seconds"] > 0
        assert 0 < body["ttl_remaining_seconds"] <= body["ttl_seconds"]


@pytest.mark.asyncio
async def test_prewarm_rejects_non_claude_models():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/chat/completions/prewarm",
            headers=headers,
            json={"model": "mock", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "prewarm_unsupported_model"


@pytest.mark.asyncio
async def test_prewarm_rejects_when_autopilot_disabled():
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Upstream-Key": "sk-ant-byok",
    }
    original = main_mod.state.settings.at_cache_autopilot_enabled
    main_mod.state.settings.at_cache_autopilot_enabled = False
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/v1/chat/completions/prewarm",
                headers=headers,
                json={
                    "model": "claude-3-5-sonnet-latest",
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            assert res.status_code == 400
            assert res.json()["error"]["code"] == "cache_autopilot_disabled"
    finally:
        main_mod.state.settings.at_cache_autopilot_enabled = original


@pytest.mark.asyncio
async def test_prewarm_forces_max_tokens_one_and_meters_separately_from_cache_miss():
    captured: list[dict] = []
    main_mod.state.anthropic = AnthropicProvider(
        "sk-ant-env", client=httpx.AsyncClient(transport=_anthropic_transport(captured))
    )
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Upstream-Key": "sk-ant-byok",
        "X-Ohm-Session": "conv-prewarm-1",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        before = (
            await client.get("/v1/usage", headers={"Authorization": "Bearer sk-at-dev"})
        ).json()

        res = await client.post(
            "/v1/chat/completions/prewarm",
            headers=headers,
            json={
                "model": "claude-3-5-sonnet-latest",
                "messages": [
                    {"role": "system", "content": "You are a coding agent."},
                    {"role": "user", "content": "read foo.py"},
                ],
                "max_tokens": 4096,  # must be overridden to 1 for the prewarm call
            },
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "warmed"
        assert body["session_id"] == "conv-prewarm-1"

        assert captured[0]["max_tokens"] == 1

        after = (
            await client.get("/v1/usage", headers={"Authorization": "Bearer sk-at-dev"})
        ).json()
        # Prewarm spend is tracked on its own rail...
        assert after["prewarm_tokens"] > before["prewarm_tokens"]
        # ...and never inflates the real cache_hit/cache_miss counters a
        # tenant uses to judge Ohm's own exact-replay savings.
        assert after["cache_miss_tokens"] == before["cache_miss_tokens"]
        assert after["cache_hit_tokens"] == before["cache_hit_tokens"]


@pytest.mark.asyncio
async def test_prewarm_never_writes_ohms_own_exact_replay_cache():
    captured: list[dict] = []
    main_mod.state.anthropic = AnthropicProvider(
        "sk-ant-env", client=httpx.AsyncClient(transport=_anthropic_transport(captured))
    )
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Upstream-Key": "sk-ant-byok",
    }
    messages = [{"role": "user", "content": "prewarm-then-real-turn"}]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prewarm_res = await client.post(
            "/v1/chat/completions/prewarm",
            headers=headers,
            json={"model": "claude-3-5-sonnet-latest", "messages": messages},
        )
        assert prewarm_res.status_code == 200

        real = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "claude-3-5-sonnet-latest", "messages": messages},
        )
        # The prewarm call must never have populated the real exact-replay
        # cache entry for this same request — it should still be a MISS.
        assert real.headers.get("x-at-cache") == "MISS"
