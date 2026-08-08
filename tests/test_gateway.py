import json

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from tests.app_state import wire_memory_app_state


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["ok"] is True


@pytest.mark.asyncio
async def test_chat_cache_hit():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": "ping-cache"}],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert miss.status_code == 200
        assert miss.headers.get("x-at-cache") == "MISS"
        assert miss.headers.get("x-at-cache-purpose") == "identical-request-replay"
        hit = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache") == "HIT"
        assert hit.headers.get("x-at-cache-purpose") == "identical-request-replay"
        assert hit.json()["choices"][0]["message"]["content"].startswith("[mock:")


@pytest.mark.asyncio
async def test_tools_are_forwarded_and_change_the_cache_key():
    """Regression guard for the tools passthrough fix: two requests with
    identical messages but different tool definitions must never collide on
    the same exact-replay cache entry, and requests without tools at all
    must keep the exact same digest/HIT behavior as before tools existed."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    base_messages = [{"role": "user", "content": "what's the weather"}]
    tool_a = [{"name": "get_weather", "description": "a", "input_schema": {"type": "object"}}]
    tool_b = [{"name": "get_weather", "description": "b", "input_schema": {"type": "object"}}]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        no_tools = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": base_messages},
        )
        assert no_tools.headers.get("x-at-cache") == "MISS"

        with_tool_a = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": base_messages, "tools": tool_a},
        )
        # Different extras (tools present) than the tool-less call above —
        # must not spuriously HIT against it.
        assert with_tool_a.headers.get("x-at-cache") == "MISS"

        with_tool_a_again = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": base_messages, "tools": tool_a},
        )
        assert with_tool_a_again.headers.get("x-at-cache") == "HIT"

        with_tool_b = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": base_messages, "tools": tool_b},
        )
        # Different tool definitions → different digest, never a HIT against tool_a.
        assert with_tool_b.headers.get("x-at-cache") == "MISS"

        no_tools_again = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": base_messages},
        )
        # Tool-less requests are unaffected by any of the above.
        assert no_tools_again.headers.get("x-at-cache") == "HIT"


@pytest.mark.asyncio
async def test_rate_limit_and_usage():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "mock", "messages": [{"role": "user", "content": "u"}]},
        )
        usage = await client.get("/v1/usage", headers=headers)
        assert usage.status_code == 200
        body = usage.json()
        assert body["requests"] >= 1
        skus = await client.get("/v1/enterprise/skus", headers=headers)
        assert skus.status_code == 200
        assert any(s["id"] == "payg-cache-arbitrage" for s in skus.json()["skus"])
        assert "today_requests" in body


@pytest.mark.asyncio
async def test_stream_meters_usage_chunk():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        before = (await client.get("/v1/usage", headers=headers)).json()
        res = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={
                "model": "mock",
                "stream": True,
                "messages": [{"role": "user", "content": "stream-me"}],
            },
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")
        body = res.text
        assert "data: [DONE]" in body
        assert '"usage"' in body
        after = (await client.get("/v1/usage", headers=headers)).json()
        assert after["requests"] >= before["requests"] + 1
        assert after["cache_miss_tokens"] > before["cache_miss_tokens"]


@pytest.mark.asyncio
async def test_issue_tenant_and_suspend():
    transport = ASGITransport(app=app)
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        issued = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={
                "plan": "payg",
                "label": "fake-customer",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert issued.status_code == 200
        api_key = issued.json()["api_key"]
        tenant_id = issued.json()["tenant"]["tenant_id"]
        assert issued.json()["tenant"]["terms_version"]
        assert issued.json()["tenant"]["dpa_version"]
        cust = {"Authorization": f"Bearer {api_key}"}
        ok = await client.post(
            "/v1/chat/completions",
            headers=cust,
            json={"model": "mock", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert ok.status_code == 200
        suspended = await client.post(
            f"/v1/admin/tenants/{tenant_id}/status",
            headers=admin,
            json={"status": "suspended"},
        )
        assert suspended.status_code == 200
        blocked = await client.post(
            "/v1/chat/completions",
            headers=cust,
            json={"model": "mock", "messages": [{"role": "user", "content": "hi2"}]},
        )
        assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_savings_dashboard():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": "savings-ping"}],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/v1/chat/completions", headers=headers, json=payload)
        await client.post("/v1/chat/completions", headers=headers, json=payload)
        sav = await client.get("/v1/savings", headers=headers)
        assert sav.status_code == 200
        body = sav.json()
        assert "estimated_upstream_avoided_usd" in body
        assert "estimated_provider_avoided_usd" in body
        assert "pipe_rent_usd" in body
        assert "roi_ratio" in body
        assert body.get("estimate_only") is True
        assert body["cache_hit_ratio"] >= 0
        # Provider estimate uses blended list rate (≥ pipe-proxy miss rent).
        assert body["estimated_provider_avoided_usd"] >= body.get(
            "estimated_pipe_proxy_avoided_usd", 0
        )
        # Third ledger rail (docs/CACHE_AUTOPILOT.md) present even at zero.
        assert body["provider_cache_read_tokens"] == 0.0
        assert body["estimated_provider_cache_savings_usd"] == 0.0


@pytest.mark.asyncio
async def test_savings_dashboard_reports_upstream_provider_cache_rail():
    import httpx

    import at_utility.main as main_mod
    from at_utility.providers import AnthropicProvider

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "ok"}],
                "usage": {
                    "input_tokens": 5,
                    "output_tokens": 2,
                    "cache_read_input_tokens": 4000,
                },
            },
        )

    main_mod.state.anthropic = AnthropicProvider(
        "sk-ant-env", client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev", "X-Ohm-Upstream-Key": "sk-ant-byok"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={
                "model": "claude-3-5-sonnet-latest",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
        assert res.status_code == 200
        sav = await client.get("/v1/savings", headers=headers)
        body = sav.json()
        assert body["provider_cache_read_tokens"] == 4000.0
        assert body["estimated_provider_cache_savings_usd"] > 0
        # Distinct from — never summed with — Ohm's own exact-replay rail.
        assert body["estimated_provider_avoided_usd"] == 0.0


@pytest.mark.asyncio
async def test_no_store_skips_cache_write():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": "no-store-ping"}],
        "cache_control": "no_store",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert first.status_code == 200
        assert first.headers.get("x-at-cache") == "BYPASS"
        second = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert second.status_code == 200
        assert second.headers.get("x-at-cache") == "BYPASS"


@pytest.mark.asyncio
async def test_compliance_policy_shape():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/compliance/policy", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert "cold_email" in body["blocked_purposes"]
        assert body["allow_cache_training"] is False
        assert body["max_chars_per_source"] == 4000
        assert body["terms"]["terms_version"]
        assert "copyright_excerpt_caps" in body["adjacent_frameworks"]
        assert body["copyright"]["version"] == "copyright-2026-08-07"
        assert body["copyright"]["dmca_contact"] == "partners@withohm.dev"
        assert body["copyright"]["excerpt_caps"]["client_cannot_raise_ceiling"] is True
        assert body["copyright"]["claims"] == "controls_not_certification"
        assert "docs/copyright" in body["copyright"]["policy_url"]


@pytest.mark.asyncio
async def test_admin_ops_snapshot():
    transport = ASGITransport(app=app)
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/admin/ops", headers=admin)
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert body["redis_ok"] is True
        assert body["stripe_meter_dlq_len"] == 0
        assert "global" in body
        denied = await client.get(
            "/v1/admin/ops", headers={"Authorization": "Bearer sk-not-admin"}
        )
        assert denied.status_code == 403


@pytest.mark.asyncio
async def test_issue_tenant_requires_terms_ack():
    transport = ASGITransport(app=app)
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={"plan": "payg", "label": "no-ack"},
        )
        assert denied.status_code == 400
