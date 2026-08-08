"""Unit tests for the breakpoint autopilot (docs/CACHE_AUTOPILOT.md)."""

import pytest

from at_utility.cache_autopilot import (
    apply_cache_autopilot,
    build_cache_units,
    resolve_session_id,
)
from at_utility.config import Settings
from at_utility.redis_store import MemoryStore


def _settings(**overrides) -> Settings:
    return Settings(**overrides)


def test_resolve_session_id_prefers_explicit_header():
    sid = resolve_session_id(
        header="conv-123",
        body_session="ignored",
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert sid == "conv-123"


def test_resolve_session_id_stable_across_growing_transcript():
    messages_turn1 = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "hello"},
    ]
    messages_turn2 = messages_turn1 + [
        {"role": "assistant", "content": "hi!"},
        {"role": "user", "content": "another question"},
    ]
    sid1 = resolve_session_id(
        header=None, body_session=None, tenant="t1", model="claude-x", messages=messages_turn1
    )
    sid2 = resolve_session_id(
        header=None, body_session=None, tenant="t1", model="claude-x", messages=messages_turn2
    )
    assert sid1 == sid2


def test_build_cache_units_orders_tools_before_messages():
    units = build_cache_units(
        tools=[{"name": "get_weather"}],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert [u.kind for u in units] == ["tools", "message"]


@pytest.mark.asyncio
async def test_first_turn_has_no_stable_prefix():
    store = MemoryStore()
    result = await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
    )
    assert result.status == "no_stable_prefix"
    assert result.messages[0]["content"] == "sys"  # untouched, still a plain string


@pytest.mark.asyncio
async def test_second_turn_injects_breakpoint_on_last_stable_message():
    store = MemoryStore()
    turn1 = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
    await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=turn1,
    )
    turn2 = turn1 + [
        {"role": "assistant", "content": "hello!"},
        {"role": "user", "content": "follow-up"},
    ]
    result = await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=turn2,
    )
    assert result.status == "injected"
    assert result.stable_prefix_units == 2  # system + first user message
    # Breakpoint lands on the *last stable* message (index 1: first user turn),
    # not on the newly appended, per-turn-varying tail.
    injected = result.messages[1]["content"]
    assert isinstance(injected, list)
    assert injected[-1]["cache_control"] == {"type": "ephemeral"}
    # Original input list must not be mutated.
    assert turn2[1]["content"] == "hi"
    # Untouched tail messages stay as plain strings.
    assert result.messages[2]["content"] == "hello!"
    assert result.messages[3]["content"] == "follow-up"


@pytest.mark.asyncio
async def test_breakpoint_not_repeated_inside_lookback_window():
    store = MemoryStore()
    settings = _settings(at_cache_autopilot_lookback_units=16)
    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
    await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    messages = messages + [
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
    ]
    first = await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    assert first.status == "injected"

    messages = messages + [
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
    ]
    second = await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    # Still well within the lookback window from the first breakpoint —
    # Anthropic will still find it, no need to spend another one.
    assert second.status == "unchanged"


@pytest.mark.asyncio
async def test_breakpoint_refreshed_once_lookback_window_would_miss():
    store = MemoryStore()
    settings = _settings(at_cache_autopilot_lookback_units=2)
    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
    await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    messages = messages + [{"role": "assistant", "content": "a1"}, {"role": "user", "content": "u2"}]
    first = await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    assert first.status == "injected"

    messages = messages + [{"role": "assistant", "content": "a2"}, {"role": "user", "content": "u3"}]
    second = await apply_cache_autopilot(
        store=store,
        settings=settings,
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    # Small lookback (2) forces a refreshed breakpoint before Anthropic's own
    # window would age the old one out.
    assert second.status == "injected"


@pytest.mark.asyncio
async def test_client_managed_cache_control_is_never_double_injected():
    store = MemoryStore()
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "sys", "cache_control": {"type": "ephemeral"}}
            ],
        },
        {"role": "user", "content": "hi"},
    ]
    result = await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    assert result.status == "client_managed"
    assert result.messages is messages


@pytest.mark.asyncio
async def test_disabled_via_settings_is_a_pure_noop():
    store = MemoryStore()
    messages = [{"role": "user", "content": "hi"}]
    result = await apply_cache_autopilot(
        store=store,
        settings=_settings(at_cache_autopilot_enabled=False),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=None,
        messages=messages,
    )
    assert result.status == "disabled"
    assert result.messages is messages


@pytest.mark.asyncio
async def test_tools_only_prefix_change_injects_on_tools_unit():
    store = MemoryStore()
    tools = [{"name": "get_weather", "description": "d", "input_schema": {"type": "object"}}]
    await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=tools,
        messages=[{"role": "user", "content": "first message"}],
    )
    # Same tools, completely different message content → only the tools unit
    # (index 0) remains stable.
    result = await apply_cache_autopilot(
        store=store,
        settings=_settings(),
        tenant="t1",
        model="claude-3-5-sonnet-latest",
        session_id="conv-1",
        tools=tools,
        messages=[{"role": "user", "content": "a totally different opening message"}],
    )
    assert result.status == "injected"
    assert result.tools[-1]["cache_control"] == {"type": "ephemeral"}
    # Original tools list untouched.
    assert "cache_control" not in tools[-1]
