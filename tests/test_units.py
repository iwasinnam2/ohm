from at_utility.billing import arbitrage_summary
from at_utility.cache import cache_key_for_request
from at_utility.ingest import inject_context_messages
from at_utility.stripe_billing import apply_webhook_to_status


def test_cache_key_stable():
    a = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "x"}]
    )
    b = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "x"}]
    )
    assert a == b
    assert a.startswith("at:t:cache:")


def test_inject_context():
    out = inject_context_messages([{"role": "user", "content": "hi"}], "# doc")
    assert out[0]["role"] == "system"
    assert "WEB CONTEXT" in out[0]["content"]
    assert "PUBLIC web excerpts" in out[0]["content"]
    assert out[1]["content"] == "hi"


def test_arbitrage_summary():
    s = arbitrage_summary(
        {"cache_hit_usd": 9.0, "cache_miss_usd": 1.0, "fetch_usd": 0.0, "enterprise_monthly_usd": 2500}
    )
    assert s["revenue_usd"] == 10.0
    assert s["estimated_high_margin_usd"] == 9.0
    assert s["cache_hit_share"] == 0.9


def test_stripe_webhook_status_map():
    assert apply_webhook_to_status("customer.subscription.deleted") == "suspended"
    assert apply_webhook_to_status("checkout.session.completed") == "active"
    assert apply_webhook_to_status("customer.created") is None


def test_billing_model_constant():
    from at_utility.stripe_billing import BILLING_MODEL

    assert BILLING_MODEL == "seat_plus_meters"


def test_provider_byok_resolve():
    from at_utility.providers import (
        MockProvider,
        OpenAIProvider,
        provider_key_available,
        resolve_provider,
    )

    mock = MockProvider()
    shell = OpenAIProvider("", "https://api.openai.com/v1")
    assert not provider_key_available(
        "gpt-4o-mini",
        upstream_key="",
        openai=shell,
        anthropic=None,
        allow_env_fallback=True,
    )
    assert provider_key_available(
        "gpt-4o-mini",
        upstream_key="sk-test",
        openai=shell,
        anthropic=None,
        allow_env_fallback=False,
    )
    p, model = resolve_provider(
        "gpt-4o-mini",
        openai=shell,
        anthropic=None,
        mock=mock,
        fallback="mock",
        upstream_key="sk-customer",
        allow_env_fallback=False,
    )
    assert model == "gpt-4o-mini"
    assert p._api_key == "sk-customer"  # type: ignore[attr-defined]
    m, mid = resolve_provider(
        "mock",
        openai=shell,
        anthropic=None,
        mock=mock,
        fallback="mock",
        upstream_key="",
        allow_env_fallback=False,
    )
    assert mid == "mock"
    assert m is mock


def test_stripe_resolve_checkout_urls():
    from at_utility.config import Settings
    from at_utility.stripe_billing import resolve_checkout_urls

    s = Settings(
        stripe_checkout_success_url="https://withohm.dev/billing/success",
        stripe_checkout_cancel_url="https://withohm.dev/billing/cancel",
    )
    ok_s, ok_c = resolve_checkout_urls(
        s, "https://example.com/billing/success", "https://example.com/x"
    )
    assert ok_s == "https://withohm.dev/billing/success"
    assert ok_c == "https://withohm.dev/billing/cancel"


def test_design_partner_plan_fields():
    from at_utility.tenants import TenantRecord

    now = 1_700_000_000
    r = TenantRecord(
        tenant_id="t1",
        plan="design_partner",
        status="active",
        key_prefix="sk-at",
        created_at=now,
        expires_at=now + 10,
        soft_quota_usd=50.0,
    )
    assert not r.is_expired(now)
    assert r.is_expired(now + 10)
