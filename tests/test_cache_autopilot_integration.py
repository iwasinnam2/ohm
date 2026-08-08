"""End-to-end: breakpoint autopilot wired into POST /v1/chat/completions."""

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
                "usage": {"input_tokens": 5, "output_tokens": 2},
            },
        )

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_second_turn_gets_an_injected_breakpoint_end_to_end():
    captured: list[dict] = []
    main_mod.state.anthropic = AnthropicProvider(
        "sk-ant-env", client=httpx.AsyncClient(transport=_anthropic_transport(captured))
    )
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Upstream-Key": "sk-ant-byok",
        "X-Ohm-Session": "conv-e2e-1",
    }
    turn1_messages = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": "read file foo.py"},
    ]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "claude-3-5-sonnet-latest", "messages": turn1_messages},
        )
        assert r1.status_code == 200
        assert r1.headers.get("x-ohm-cache-autopilot") == "no_stable_prefix"
        assert "system" not in captured[0] or not any(
            isinstance(b, dict) and "cache_control" in b
            for b in (captured[0].get("system") or [])
            if isinstance(captured[0].get("system"), list)
        )

        turn2_messages = turn1_messages + [
            {"role": "assistant", "content": "reading..."},
            {"role": "user", "content": "now summarize it"},
        ]
        r2 = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "claude-3-5-sonnet-latest", "messages": turn2_messages},
        )
        assert r2.status_code == 200
        assert r2.headers.get("x-ohm-cache-autopilot") == "injected"

    assert len(captured) == 2
    second_body = captured[1]
    # The breakpoint lands on the last *stable* message (the first user
    # turn) — its content was upgraded from a plain string to a
    # cache_control-bearing content-block array.
    second_messages = second_body["messages"]
    first_user_msg = next(m for m in second_messages if m["content"] not in ("reading...", "now summarize it") and m["role"] == "user")
    assert isinstance(first_user_msg["content"], list)
    assert first_user_msg["content"][-1]["cache_control"] == {"type": "ephemeral"}
    # Ohm's own exact-replay cache key is unaffected: two structurally
    # identical requests should still be a plain byte-for-byte HIT candidate
    # (verified separately by test_gateway.py's exact-match suite).
