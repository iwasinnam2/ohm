"""Money-path integrity: edge-hit metering, Stripe idempotency, caps, checkout RL."""

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from at_utility.metering import Meter, billable_1k_units
from at_utility.providers import MockProvider
from at_utility.redis_store import MemoryStore
from at_utility.tenants import TenantRegistry
import at_utility.main as main_mod
import at_utility.metering as metering_mod


@pytest.fixture(autouse=True)
async def _mem_state():
    get_settings.cache_clear()
    store = MemoryStore()
    settings = get_settings()
    # Never touch real Stripe from tests
    settings.stripe_secret_key = ""
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


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# billable units / ledger math
# ---------------------------------------------------------------------------


def test_billable_units_zero_tokens_bill_nothing():
    assert billable_1k_units(0) == 0
    assert billable_1k_units(-5) == 0


def test_billable_units_ceil():
    assert billable_1k_units(1) == 1
    assert billable_1k_units(1000) == 1
    assert billable_1k_units(1001) == 2
    assert billable_1k_units(2500) == 3


@pytest.mark.asyncio
async def test_ledger_usd_matches_stripe_ceil_math():
    """Redis ledger USD must equal units * price (what Stripe invoices)."""
    settings = main_mod.state.settings
    meter = main_mod.state.meter
    event = await meter.record_chat("tenant_test", cache_hit=True, total_tokens=1500)
    assert event.billable_units == 2
    assert event.billed_usd == pytest.approx(2 * settings.at_price_per_1k_tokens_hit)
    snap = await meter.snapshot("tenant_test")
    assert snap["cache_hit_usd"] == pytest.approx(event.billed_usd)


@pytest.mark.asyncio
async def test_zero_token_chat_records_request_but_bills_zero():
    meter = main_mod.state.meter
    event = await meter.record_chat("tenant_zero", cache_hit=False, total_tokens=0)
    assert event.billable_units == 0
    assert event.billed_usd == 0.0
    snap = await meter.snapshot("tenant_zero")
    assert snap["requests"] == 1.0
    assert snap["cache_miss_usd"] == 0.0


# ---------------------------------------------------------------------------
# Stripe meter idempotency identifier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_meter_passes_idempotency_identifier(monkeypatch):
    captured: list[dict] = []

    def fake_report(settings, *, event_name, stripe_customer_id, value, identifier=""):
        captured.append(
            {
                "event_name": event_name,
                "customer": stripe_customer_id,
                "value": value,
                "identifier": identifier,
            }
        )
        return True

    monkeypatch.setattr(
        metering_mod.stripe_billing, "report_meter_event", fake_report
    )
    meter = main_mod.state.meter
    event = await meter.record_chat(
        "tenant_idem", cache_hit=True, total_tokens=500, stripe_customer_id="cus_x"
    )
    assert event.stripe_synced is True
    assert len(captured) == 1
    assert captured[0]["value"] == 1
    assert captured[0]["identifier"].startswith("tenant_idem:cache_hit:")
    # Distinct logical events must carry distinct identifiers
    await meter.record_chat(
        "tenant_idem", cache_hit=True, total_tokens=500, stripe_customer_id="cus_x"
    )
    assert captured[1]["identifier"] != captured[0]["identifier"]


@pytest.mark.asyncio
async def test_zero_tokens_never_fire_stripe(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        metering_mod.stripe_billing,
        "report_meter_event",
        lambda *a, **k: calls.append("fired") or True,
    )
    meter = main_mod.state.meter
    event = await meter.record_chat(
        "tenant_zero2", cache_hit=True, total_tokens=0, stripe_customer_id="cus_x"
    )
    assert event.billable_units == 0
    assert calls == []


# ---------------------------------------------------------------------------
# /internal/edge-hit — metering + enforcement gate for the Rust edge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_edge_hit_disabled_without_secret():
    main_mod.state.settings.at_edge_shared_secret = ""
    async with _client() as client:
        res = await client.post(
            "/internal/edge-hit",
            headers={"Authorization": "Bearer sk-at-dev"},
            json={"total_tokens": 100},
        )
        assert res.status_code == 503


@pytest.mark.asyncio
async def test_edge_hit_rejects_wrong_secret():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    async with _client() as client:
        res = await client.post(
            "/internal/edge-hit",
            headers={
                "Authorization": "Bearer sk-at-dev",
                "X-Ohm-Edge-Secret": "wrong",
            },
            json={"total_tokens": 100},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_edge_hit_meters_cached_tokens():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    headers = {"Authorization": "Bearer sk-at-dev", "X-Ohm-Edge-Secret": "s3cret"}
    async with _client() as client:
        before = (
            await client.get("/v1/usage", headers={"Authorization": "Bearer sk-at-dev"})
        ).json()
        res = await client.post(
            "/internal/edge-hit", headers=headers, json={"total_tokens": 1200}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert body["billed_usd"] == pytest.approx(
            2 * main_mod.state.settings.at_price_per_1k_tokens_hit
        )
        after = (
            await client.get("/v1/usage", headers={"Authorization": "Bearer sk-at-dev"})
        ).json()
        assert after["requests"] >= before["requests"] + 1
        assert after["cache_hit_tokens"] >= before["cache_hit_tokens"] + 1200


@pytest.mark.asyncio
async def test_edge_hit_denies_suspended_tenant():
    """A suspended tenant must never be served a cached completion at the edge."""
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with _client() as client:
        issued = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={"plan": "payg", "label": "edge-suspend", "terms_ack": True, "dpa_ack": True},
        )
        api_key = issued.json()["api_key"]
        tenant_id = issued.json()["tenant"]["tenant_id"]
        await client.post(
            f"/v1/admin/tenants/{tenant_id}/status",
            headers=admin,
            json={"status": "suspended"},
        )
        res = await client.post(
            "/internal/edge-hit",
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Ohm-Edge-Secret": "s3cret",
            },
            json={"total_tokens": 100},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_edge_hit_enforces_request_cap():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with _client() as client:
        issued = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={
                "plan": "payg",
                "label": "edge-cap",
                "terms_ack": True,
                "dpa_ack": True,
                "request_cap": 1,
            },
        )
        api_key = issued.json()["api_key"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-Ohm-Edge-Secret": "s3cret",
        }
        first = await client.post(
            "/internal/edge-hit", headers=headers, json={"total_tokens": 100}
        )
        assert first.status_code == 200
        second = await client.post(
            "/internal/edge-hit", headers=headers, json={"total_tokens": 100}
        )
        assert second.status_code == 403
        assert second.json()["error"]["code"] == "request_cap"


# ---------------------------------------------------------------------------
# request_cap on the chat path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_cap_enforced_on_chat():
    admin = {"Authorization": "Bearer sk-at-dev"}
    async with _client() as client:
        issued = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={
                "plan": "payg",
                "label": "capped",
                "terms_ack": True,
                "dpa_ack": True,
                "request_cap": 1,
            },
        )
        api_key = issued.json()["api_key"]
        cust = {"Authorization": f"Bearer {api_key}"}
        payload = {"model": "mock", "messages": [{"role": "user", "content": "hi"}]}
        first = await client.post("/v1/chat/completions", headers=cust, json=payload)
        assert first.status_code == 200
        second = await client.post("/v1/chat/completions", headers=cust, json=payload)
        assert second.status_code == 403
        assert second.json()["error"]["code"] == "request_cap"


# ---------------------------------------------------------------------------
# checkout rate limit (IP token bucket: 0.1 rps, burst 3)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# fetch soft-cap: only a paid invoice (or privileged plan) unlocks
# ---------------------------------------------------------------------------


async def _issue_payg(client: AsyncClient) -> tuple[str, str]:
    issued = await client.post(
        "/v1/admin/tenants",
        headers={"Authorization": "Bearer sk-at-dev"},
        json={"plan": "payg", "label": "fence", "terms_ack": True, "dpa_ack": True},
    )
    body = issued.json()
    return body["api_key"], body["tenant"]["tenant_id"]


@pytest.mark.asyncio
async def test_metered_spend_does_not_unlock_usage():
    """revenue_usd > 0 must NOT lift the fetch cap — only invoice.paid does."""
    async with _client() as client:
        api_key, tenant_id = await _issue_payg(client)
        # Simulate un-invoiced metered spend
        await main_mod.state.meter.record_chat(
            tenant_id, cache_hit=False, total_tokens=5000
        )
        usage = (
            await client.get(
                "/v1/usage", headers={"Authorization": f"Bearer {api_key}"}
            )
        ).json()
        assert usage["revenue_usd"] > 0
        assert usage["usage_unlocked"] is False
        # A paid invoice is what unlocks
        await main_mod.state.tenants.attach_stripe(tenant_id, billing_paid=True)
        usage = (
            await client.get(
                "/v1/usage", headers={"Authorization": f"Bearer {api_key}"}
            )
        ).json()
        assert usage["usage_unlocked"] is True


@pytest.mark.asyncio
async def test_fetch_cap_429_despite_metered_spend():
    main_mod.state.settings.at_free_tier_fetch_cap_day = 1
    async with _client() as client:
        api_key, tenant_id = await _issue_payg(client)
        await main_mod.state.meter.record_chat(
            tenant_id, cache_hit=False, total_tokens=5000
        )
        res = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "mock",
                "messages": [{"role": "user", "content": "hi"}],
                "fetch_web_context": True,
                "web_urls": ["https://a.example.com", "https://b.example.com"],
                "web_purpose": "public_web_retrieval",
            },
        )
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "fetch_cap_day"


# ---------------------------------------------------------------------------
# BYOK: env-key fallback is closed for customer (payg) plans by default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payg_cannot_burn_env_upstream_keys():
    from at_utility.providers import OpenAIProvider

    assert main_mod.state.settings.at_byok_allow_env_fallback is False
    main_mod.state.openai = OpenAIProvider(
        "sk-env-operator-key", "https://api.openai.com/v1"
    )
    async with _client() as client:
        api_key, _ = await _issue_payg(client)
        res = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "upstream_key_required"


# ---------------------------------------------------------------------------
# Stripe meter DLQ: failed events are queued and replayed, never lost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failed_meter_event_dead_letters_and_replays(monkeypatch):
    from at_utility.metering import STRIPE_METER_DLQ_KEY

    main_mod.state.settings.stripe_secret_key = "sk_test_dlq"
    meter = main_mod.state.meter
    store = main_mod.state.store

    monkeypatch.setattr(
        metering_mod.stripe_billing, "report_meter_event", lambda *a, **k: False
    )
    event = await meter.record_chat(
        "tenant_dlq", cache_hit=True, total_tokens=1500, stripe_customer_id="cus_dlq"
    )
    assert event.stripe_synced is False
    assert await store.list_len(STRIPE_METER_DLQ_KEY) == 1

    replayed: list[dict] = []

    def ok_report(settings, *, event_name, stripe_customer_id, value, identifier=""):
        replayed.append(
            {"event_name": event_name, "value": value, "identifier": identifier}
        )
        return True

    monkeypatch.setattr(metering_mod.stripe_billing, "report_meter_event", ok_report)
    count = await meter.replay_stripe_dlq()
    assert count == 1
    assert await store.list_len(STRIPE_METER_DLQ_KEY) == 0
    # Same identifier as the original attempt — Stripe dedup keeps it single-billed
    assert replayed[0]["identifier"].startswith("tenant_dlq:cache_hit:")
    assert replayed[0]["value"] == 2


@pytest.mark.asyncio
async def test_replay_requeues_on_persistent_failure(monkeypatch):
    from at_utility.metering import STRIPE_METER_DLQ_KEY

    main_mod.state.settings.stripe_secret_key = "sk_test_dlq"
    meter = main_mod.state.meter
    store = main_mod.state.store
    monkeypatch.setattr(
        metering_mod.stripe_billing, "report_meter_event", lambda *a, **k: False
    )
    await meter.record_fetch("tenant_dlq2", count=3, stripe_customer_id="cus_dlq2")
    assert await store.list_len(STRIPE_METER_DLQ_KEY) == 1
    count = await meter.replay_stripe_dlq()
    assert count == 0
    assert await store.list_len(STRIPE_METER_DLQ_KEY) == 1


# ---------------------------------------------------------------------------
# delinquency sweep: dunning deadline enforced without waiting for a request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delinquency_sweep_suspends_expired_tenants():
    import time as _time

    async with _client() as client:
        api_key, tenant_id = await _issue_payg(client)
        await main_mod.state.tenants.attach_stripe(
            tenant_id,
            billing_delinquent_since=int(_time.time()) - 20 * 86400,
        )
        suspended = await main_mod.state.tenants.sweep_delinquent(14)
        assert suspended == 1
        res = await client.get(
            "/v1/usage", headers={"Authorization": f"Bearer {api_key}"}
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_delinquency_sweep_spares_recent_delinquents():
    import time as _time

    async with _client() as client:
        _, tenant_id = await _issue_payg(client)
        await main_mod.state.tenants.attach_stripe(
            tenant_id,
            billing_delinquent_since=int(_time.time()) - 3 * 86400,
        )
        assert await main_mod.state.tenants.sweep_delinquent(14) == 0


@pytest.mark.asyncio
async def test_checkout_rate_limited_after_burst():
    async with _client() as client:
        statuses = []
        for _ in range(4):
            res = await client.post(
                "/v1/billing/checkout",
                json={"plan": "payg", "email": "rl@test.dev"},
            )
            statuses.append(res.status_code)
        # First 3 pass the bucket (then fail on terms/stripe config — not 429);
        # the 4th must be throttled.
        assert all(s != 429 for s in statuses[:3])
        assert statuses[3] == 429
        assert (
            (await client.post("/v1/billing/checkout", json={"plan": "payg"}))
            .status_code
            == 429
        )
