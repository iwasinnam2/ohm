"""Money-path integrity: edge-hit metering, Stripe idempotency, caps, checkout RL."""

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from at_utility.metering import billable_1k_units
import at_utility.main as main_mod
import at_utility.metering as metering_mod
from tests.app_state import wire_memory_app_state


@pytest.fixture(autouse=True)
async def _mem_state():
    # Never touch real Stripe from tests
    store = await wire_memory_app_state(clear_stripe=True)
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


# ---------------------------------------------------------------------------
# rate card v2: commit tiers + retired credit pack
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_topup_is_retired_with_commit_guidance():
    async with _client() as client:
        res = await client.post(
            "/v1/billing/topup",
            headers={"Authorization": "Bearer sk-at-dev"},
            json={},
        )
        assert res.status_code == 410
        err = res.json()["error"]
        assert err["code"] == "credit_pack_retired"
        assert err["details"]["commit_tiers"] == ["c29", "c99", "c499"]


@pytest.mark.asyncio
async def test_checkout_rejects_unknown_commit_tier():
    async with _client() as client:
        res = await client.post(
            "/v1/billing/checkout",
            json={"plan": "payg", "commit": "c9000", "email": "x@test.dev"},
        )
        assert res.status_code == 400
        assert "commit" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_checkout_passes_commit_to_session(monkeypatch):
    from at_utility import stripe_billing as sb

    captured: dict = {}
    main_mod.state.settings.stripe_secret_key = "sk_test_x"
    main_mod.state.settings.stripe_price_payg = "price_seat"
    monkeypatch.setattr(sb, "stripe_configured", lambda s: True)

    def fake_session(settings, *, plan, success_url, cancel_url,
                     tenant_id="", pending_id="", customer_email="", commit=""):
        captured.update({"plan": plan, "commit": commit, "pending_id": pending_id})
        return {"id": "cs_x", "url": "https://checkout.test", "plan": plan}

    monkeypatch.setattr(sb, "create_checkout_session", fake_session)
    async with _client() as client:
        res = await client.post(
            "/v1/billing/checkout",
            json={
                "plan": "payg",
                "commit": "c99",
                "email": "commit@test.dev",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert res.status_code == 200
        assert captured["plan"] == "payg"
        assert captured["commit"] == "c99"
        assert captured["pending_id"].startswith("pend_")
        assert "api_key" not in res.json()


def test_commit_tier_detected_from_invoice_lines():
    from at_utility import stripe_billing as sb
    from at_utility.config import get_settings

    settings = get_settings()
    settings.stripe_price_commit_c29 = "price_c29"
    settings.stripe_price_commit_c99 = "price_c99"
    invoice = {
        "id": "in_test",
        "lines": {
            "data": [
                {"price": {"id": "price_meter_hit"}},
                {"price": {"id": "price_c99"}},
            ]
        },
    }
    assert sb.commit_tier_for_invoice(settings, invoice) == "c99"
    # Newer API shape: pricing.price_details.price instead of price.id
    invoice_new = {
        "id": "in_test2",
        "lines": {
            "data": [{"pricing": {"price_details": {"price": "price_c29"}}}]
        },
    }
    assert sb.commit_tier_for_invoice(settings, invoice_new) == "c29"
    assert sb.commit_tier_for_invoice(settings, {"id": "in_x", "lines": {"data": []}}) == ""


def test_commit_included_usd_matches_rate_card():
    import json
    from pathlib import Path

    from at_utility import stripe_billing as sb
    from at_utility.config import get_settings

    card = json.loads(
        (Path(__file__).resolve().parents[1] / "pricing" / "rate_card.v2.json")
        .read_text(encoding="utf-8")
    )
    settings = get_settings()
    for tier in card["commit_tiers"]:
        assert sb.commit_included_usd(settings, tier["id"]) == tier["included_usd"]
    assert sb.commit_included_usd(settings, "nope") == 0.0


def test_commit_grant_skips_without_stripe_config():
    from at_utility import stripe_billing as sb
    from at_utility.config import get_settings

    settings = get_settings()
    settings.stripe_secret_key = ""
    granted = sb.grant_commit_included_credit(
        settings, stripe_customer_id="cus_x", tier="c29", invoice_id="in_x"
    )
    assert granted == 0.0


def test_checkout_session_seat_only_line_items(monkeypatch):
    """Hosted Checkout must not list hit/miss/fetch as charges."""
    import sys
    import types

    from at_utility import stripe_billing as sb
    from at_utility.config import get_settings

    settings = get_settings()
    settings.stripe_secret_key = "sk_test_x"
    settings.stripe_price_payg = "price_seat"
    settings.stripe_price_meter_web_fetch = "price_fetch"
    settings.stripe_price_meter_cache_hit = "price_hit"
    settings.stripe_price_meter_cache_miss = "price_miss"
    settings.at_require_meter_prices = False
    settings.stripe_automatic_tax = False
    settings.stripe_checkout_success_url = "https://www.withohm.dev/ok"
    settings.stripe_checkout_cancel_url = "https://www.withohm.dev/cancel"

    captured: dict = {}

    class _FakeSession:
        id = "cs_test"
        url = "https://checkout.test/s"

    def _create(**params):
        captured.clear()
        captured.update(params)
        return _FakeSession()

    fake = types.ModuleType("stripe")
    fake.api_key = None
    fake.checkout = types.SimpleNamespace(
        Session=types.SimpleNamespace(create=_create)
    )
    monkeypatch.setitem(sys.modules, "stripe", fake)

    result = sb.create_checkout_session(
        settings,
        tenant_id="ten_x",
        plan="payg",
        success_url="https://www.withohm.dev/ok",
        cancel_url="https://www.withohm.dev/cancel",
        customer_email="a@test.dev",
    )
    assert result["url"] == "https://checkout.test/s"
    assert captured["line_items"] == [{"price": "price_seat", "quantity": 1}]
    assert "price_hit" not in str(captured["line_items"])
    assert "price_miss" not in str(captured["line_items"])
    assert "price_fetch" not in str(captured["line_items"])


def test_attach_meter_prices_idempotent(monkeypatch):
    from at_utility import stripe_billing as sb
    from at_utility.config import get_settings
    import sys
    import types

    settings = get_settings()
    settings.stripe_secret_key = "sk_test_x"
    settings.stripe_price_meter_web_fetch = "price_fetch"
    settings.stripe_price_meter_cache_hit = "price_hit"
    settings.stripe_price_meter_cache_miss = "price_miss"

    modify_calls: list[dict] = []

    fake = types.ModuleType("stripe")
    fake.api_key = None

    class _Sub:
        @staticmethod
        def retrieve(sub_id, expand=None):
            return {
                "id": sub_id,
                "items": {
                    "data": [
                        {"price": {"id": "price_seat"}},
                        {"price": {"id": "price_hit"}},  # already attached
                    ]
                },
            }

        @staticmethod
        def modify(sub_id, **params):
            modify_calls.append({"id": sub_id, **params})
            return {"id": sub_id}

    fake.Subscription = _Sub
    monkeypatch.setitem(sys.modules, "stripe", fake)

    n = sb.attach_meter_prices_to_subscription(settings, subscription_id="sub_x")
    assert n == 2
    assert len(modify_calls) == 1
    prices = {item["price"] for item in modify_calls[0]["items"]}
    assert prices == {"price_fetch", "price_miss"}
    assert modify_calls[0]["proration_behavior"] == "none"

    # Second call: all three meters present → no-op
    def retrieve_all(sub_id, expand=None):
        return {
            "id": sub_id,
            "items": {
                "data": [
                    {"price": {"id": "price_seat"}},
                    {"price": {"id": "price_hit"}},
                    {"price": {"id": "price_miss"}},
                    {"price": {"id": "price_fetch"}},
                ]
            },
        }

    fake.Subscription.retrieve = staticmethod(retrieve_all)
    modify_calls.clear()
    assert sb.attach_meter_prices_to_subscription(settings, subscription_id="sub_x") == 0
    assert modify_calls == []


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


@pytest.mark.asyncio
async def test_account_keys_mint_list_delete():
    """Subscribers mint/list/delete keys without re-entering checkout details."""
    from at_utility import checkout_fulfill as cf

    admin = {"Authorization": "Bearer sk-at-dev"}
    async with _client() as client:
        issued = await client.post(
            "/v1/admin/tenants",
            headers=admin,
            json={
                "plan": "payg",
                "label": "acct",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert issued.status_code == 200
        api_key = issued.json()["api_key"]
        tenant_id = issued.json()["tenant"]["tenant_id"]
        await main_mod.state.tenants.attach_stripe(
            tenant_id,
            customer_id="cus_test_keys",
            subscription_id="sub_test_keys",
            status="active",
            billing_paid=True,
        )
        headers = {"Authorization": f"Bearer {api_key}"}

        listed = await client.get("/v1/account/keys", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()["keys"]) >= 1

        minted = await client.post(
            "/v1/account/keys",
            headers=headers,
            json={"label": "ci"},
        )
        assert minted.status_code == 200
        new_key = minted.json()["api_key"]
        new_tid = minted.json()["tenant"]["tenant_id"]
        assert new_key.startswith("sk-at-")
        assert new_tid != tenant_id

        listed2 = await client.get("/v1/account/keys", headers=headers)
        ids = {k["tenant_id"] for k in listed2.json()["keys"]}
        assert tenant_id in ids and new_tid in ids

        deleted = await client.delete(
            f"/v1/account/keys/{new_tid}", headers=headers
        )
        assert deleted.status_code == 200
        assert deleted.json()["tenant"]["status"] == "revoked"

        # Revoked secret no longer authenticates
        dead = await client.get(
            "/v1/usage", headers={"Authorization": f"Bearer {new_key}"}
        )
        assert dead.status_code == 401


@pytest.mark.asyncio
async def test_checkout_fulfill_and_claim_key():
    from at_utility import checkout_fulfill as cf

    async with _client() as client:
        pending_id = cf.new_pending_id()
        await cf.save_pending(
            main_mod.state.store,
            pending_id,
            {
                "plan": "payg",
                "email": "claim@test.dev",
                "label": "claim-me",
                "terms_version": "tos-test",
                "dpa_version": "dpa-test",
            },
        )
        fulfilled = await cf.fulfill_pending_checkout(
            store=main_mod.state.store,
            tenants=main_mod.state.tenants,
            settings=main_mod.state.settings,
            session_id="cs_test_claim_1",
            pending_id=pending_id,
            customer_id="cus_claim",
            subscription_id="sub_claim",
        )
        assert fulfilled is not None
        raw_key, record = fulfilled
        assert record.stripe_customer_id == "cus_claim"
        assert record.billing_paid is True

        # Claim consumes the one-time reveal
        claim = await client.post(
            "/v1/billing/claim-key", json={"session_id": "cs_test_claim_1"}
        )
        assert claim.status_code == 200
        assert claim.json()["api_key"] == raw_key

        again = await client.post(
            "/v1/billing/claim-key", json={"session_id": "cs_test_claim_1"}
        )
        assert again.status_code == 410
