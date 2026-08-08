import json

import httpx
import pytest

from at_utility.anthropic_sse import (
    AnthropicToOpenAIStreamTranslator,
    anthropic_usage_to_openai,
    parse_anthropic_sse_block,
)
from at_utility.providers import AnthropicProvider, OpenAIProvider
from at_utility.stream_usage import approx_tokens_from_sse_lines, usage_from_sse_line


def _payload(line: str) -> dict:
    assert line.startswith("data: ")
    return json.loads(line[len("data: ") :].strip())


def test_parse_anthropic_sse_block():
    block = (
        "event: content_block_delta\n"
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}'
    )
    et, data = parse_anthropic_sse_block(block)
    assert et == "content_block_delta"
    assert data["delta"]["text"] == "Hi"


def test_translator_emits_openai_chunks_and_usage():
    t = AnthropicToOpenAIStreamTranslator("claude-3-5-sonnet-latest")
    lines: list[str] = []
    lines += t.feed_event(
        "message_start",
        {
            "type": "message_start",
            "message": {"usage": {"input_tokens": 12, "output_tokens": 0}},
        },
    )
    lines += t.feed_event(
        "content_block_delta",
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello"},
        },
    )
    lines += t.feed_event(
        "content_block_delta",
        {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": " world"},
        },
    )
    lines += t.feed_event(
        "message_delta",
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"output_tokens": 4},
        },
    )
    lines += t.feed_event("message_stop", {"type": "message_stop"})

    text_parts: list[str] = []
    role_seen = False
    for line in lines:
        if line == "data: [DONE]\n\n":
            continue
        p = _payload(line)
        choices = p.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        if delta.get("role") == "assistant":
            role_seen = True
        elif "content" in delta:
            text_parts.append(delta["content"])
        if choices[0].get("finish_reason") == "stop":
            assert delta == {}

    assert role_seen
    assert "".join(text_parts) == "Hello world"
    assert lines[-1] == "data: [DONE]\n\n"
    usage = _payload(lines[-2])["usage"]
    assert usage == {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}
    assert usage_from_sse_line(lines[-2]) == 16


def test_usage_from_sse_line_openai_shape():
    line = (
        'data: {"id":"x","object":"chat.completion.chunk","choices":[],'
        '"usage":{"prompt_tokens":3,"completion_tokens":5,"total_tokens":8}}\n'
    )
    assert usage_from_sse_line(line) == 8
    assert usage_from_sse_line("data: [DONE]\n") is None
    assert approx_tokens_from_sse_lines(["abcd"]) == 1


@pytest.mark.asyncio
async def test_openai_stream_sets_include_usage():
    captured: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        sse = (
            'data: {"id":"c","object":"chat.completion.chunk","choices":'
            '[{"index":0,"delta":{"content":"ok"},"finish_reason":null}]}\n\n'
            'data: {"id":"c","object":"chat.completion.chunk","choices":[],'
            '"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, text=sse)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = OpenAIProvider("sk-test", "https://api.openai.com/v1", client=client)
    stream = await provider.chat_completion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    chunks = [line async for line in stream]  # type: ignore[union-attr]
    await client.aclose()
    assert captured["body"]["stream"] is True
    assert captured["body"]["stream_options"]["include_usage"] is True
    assert any("total_tokens" in c for c in chunks)


@pytest.mark.asyncio
async def test_anthropic_true_stream_translation():
    anthropic_sse = (
        "event: message_start\n"
        'data: {"type":"message_start","message":{"id":"msg_1","usage":{"input_tokens":9,"output_tokens":0}}}\n\n'
        "event: content_block_delta\n"
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Yo"}}\n\n'
        "event: message_delta\n"
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":1}}\n\n'
        "event: message_stop\n"
        'data: {"type":"message_stop"}\n\n'
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert body["stream"] is True
        return httpx.Response(200, text=anthropic_sse)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = AnthropicProvider("sk-ant-test", client=client)
    stream = await provider.chat_completion(
        model="claude-3-5-sonnet-latest",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    lines = [line async for line in stream]  # type: ignore[union-attr]
    await client.aclose()

    text = "".join(
        (_payload(line)["choices"][0]["delta"].get("content") or "")
        for line in lines
        if line.startswith("data: {")
        and (_payload(line).get("choices") or [{}])[0].get("delta", {}).get("role") is None
        and "content" in (_payload(line).get("choices") or [{}])[0].get("delta", {})
    )
    assert text == "Yo"
    assert lines[-1] == "data: [DONE]\n\n"
    assert usage_from_sse_line(lines[-2]) == 10


def test_anthropic_usage_to_openai_without_cache_is_unchanged():
    """No cache tokens → identical shape to before prompt-caching support."""
    usage = anthropic_usage_to_openai(input_tokens=12, output_tokens=4)
    assert usage == {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}


def test_anthropic_usage_to_openai_includes_cache_tokens():
    usage = anthropic_usage_to_openai(
        input_tokens=50,
        output_tokens=10,
        cache_creation_input_tokens=200,
        cache_read_input_tokens=1800,
    )
    # prompt_tokens is the *full* input (input + cache_creation + cache_read),
    # matching total_input_tokens in the prompt-caching docs.
    assert usage["prompt_tokens"] == 2050
    assert usage["completion_tokens"] == 10
    assert usage["total_tokens"] == 2060
    assert usage["cache_creation_input_tokens"] == 200
    assert usage["cache_read_input_tokens"] == 1800
    assert usage["prompt_tokens_details"] == {"cached_tokens": 1800}


def test_translator_tracks_cache_tokens_from_message_start():
    t = AnthropicToOpenAIStreamTranslator("claude-3-5-sonnet-latest")
    lines: list[str] = []
    lines += t.feed_event(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "usage": {
                    "input_tokens": 5,
                    "output_tokens": 0,
                    "cache_creation_input_tokens": 100,
                    "cache_read_input_tokens": 900,
                }
            },
        },
    )
    lines += t.feed_event(
        "message_delta",
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 3}},
    )
    lines += t.feed_event("message_stop", {"type": "message_stop"})

    usage = _payload(lines[-2])["usage"]
    assert usage["prompt_tokens"] == 1005
    assert usage["cache_read_input_tokens"] == 900
    assert usage["cache_creation_input_tokens"] == 100
    assert usage["prompt_tokens_details"] == {"cached_tokens": 900}


@pytest.mark.asyncio
async def test_anthropic_build_body_preserves_system_blocks_and_tools():
    """Content-block system prompts (carrying cache_control) and tool
    definitions must reach Anthropic verbatim — previously the system
    message was force-flattened with str() and tools had no field to travel
    through at all."""
    captured: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "ok"}],
                "usage": {"input_tokens": 3, "output_tokens": 1},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = AnthropicProvider("sk-ant-test", client=client)

    system_blocks = [
        {
            "type": "text",
            "text": "You are a helpful assistant.",
            "cache_control": {"type": "ephemeral"},
        }
    ]
    tools = [
        {
            "name": "get_weather",
            "description": "Get the weather",
            "input_schema": {"type": "object", "properties": {}},
            "cache_control": {"type": "ephemeral"},
        }
    ]
    await provider.chat_completion(
        model="claude-3-5-sonnet-latest",
        messages=[
            {"role": "system", "content": system_blocks},
            {"role": "user", "content": "hi"},
        ],
        stream=False,
        tools=tools,
        tool_choice="auto",
    )
    await client.aclose()

    body = captured["body"]
    assert body["system"] == system_blocks
    assert body["tools"] == tools
    assert body["tool_choice"] == "auto"
    assert body["messages"] == [{"role": "user", "content": "hi"}]


@pytest.mark.asyncio
async def test_anthropic_build_body_merges_mixed_system_messages_without_dropping():
    """Multiple system messages are unusual, but a plain-string one followed
    (or preceded) by a content-block one must not silently drop either —
    both must land in the outbound `system` block list, in order."""
    captured: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "ok"}],
                "usage": {"input_tokens": 3, "output_tokens": 1},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = AnthropicProvider("sk-ant-test", client=client)

    cache_block = {
        "type": "text",
        "text": "Cached instructions.",
        "cache_control": {"type": "ephemeral"},
    }
    await provider.chat_completion(
        model="claude-3-5-sonnet-latest",
        messages=[
            {"role": "system", "content": "Plain string preamble."},
            {"role": "system", "content": [cache_block]},
            {"role": "user", "content": "hi"},
        ],
        stream=False,
    )
    await client.aclose()

    body = captured["body"]
    assert body["system"] == [
        {"type": "text", "text": "Plain string preamble."},
        cache_block,
    ]


@pytest.mark.asyncio
async def test_anthropic_build_body_merges_multiple_content_block_system_messages():
    """Two content-block system messages must both survive — the old code
    silently overwrote the first with the second."""
    captured: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "ok"}],
                "usage": {"input_tokens": 3, "output_tokens": 1},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = AnthropicProvider("sk-ant-test", client=client)

    block_a = {"type": "text", "text": "First block."}
    block_b = {
        "type": "text",
        "text": "Second block.",
        "cache_control": {"type": "ephemeral"},
    }
    await provider.chat_completion(
        model="claude-3-5-sonnet-latest",
        messages=[
            {"role": "system", "content": [block_a]},
            {"role": "system", "content": [block_b]},
            {"role": "user", "content": "hi"},
        ],
        stream=False,
    )
    await client.aclose()

    assert captured["body"]["system"] == [block_a, block_b]


@pytest.mark.asyncio
async def test_anthropic_non_streaming_reports_cache_tokens():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "hi there"}],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 4000,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = AnthropicProvider("sk-ant-test", client=client)
    result = await provider.chat_completion(
        model="claude-3-5-sonnet-latest",
        messages=[{"role": "user", "content": "hi"}],
        stream=False,
    )
    await client.aclose()
    assert isinstance(result, dict)
    usage = result["usage"]
    assert usage["cache_read_input_tokens"] == 4000
    assert usage["prompt_tokens"] == 4010
    assert usage["total_tokens"] == 4015
