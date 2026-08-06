import pytest

from at_utility.billing import arbitrage_summary
from at_utility.cache import cache_key_for_request, resolve_cache_tree
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
    assert a.startswith("at:t:cache:v2:")


def test_resolve_cache_tree():
    assert resolve_cache_tree() == "main"
    assert resolve_cache_tree(header="PR-842") == "pr-842"
    assert resolve_cache_tree(header="", body="agent-run-1") == "agent-run-1"
    assert resolve_cache_tree(header="hdr", body="body") == "hdr"
    with pytest.raises(ValueError):
        resolve_cache_tree(header="BAD TREE")


def test_cache_key_v3_named_tree():
    """Named trees use v3; digest matches v2 main for the same payload."""
    extras = {
        "fetch_web_context": False,
        "web_query": None,
        "web_urls": [],
        "web_purpose": None,
        "web_format": None,
        "temperature": None,
        "max_tokens": None,
        "cache_control": None,
    }
    msgs = [{"role": "user", "content": "  hello\r\nworld  "}]
    main = cache_key_for_request(
        tenant="parity", model="mock", messages=msgs, extras=extras, tree_id="main"
    )
    named = cache_key_for_request(
        tenant="parity", model="mock", messages=msgs, extras=extras, tree_id="pr-842"
    )
    assert main == (
        "at:parity:cache:v2:"
        "ea9e2e59350222baec8ed5fc7f85078ea788c48526f389bb6264ef251052db4d"
    )
    assert named == (
        "at:parity:tree:pr-842:cache:v3:"
        "ea9e2e59350222baec8ed5fc7f85078ea788c48526f389bb6264ef251052db4d"
    )
    assert named.rsplit(":", 1)[-1] == main.rsplit(":", 1)[-1]


def test_cache_key_v2_normalizes_transport_noise():
    """CRLF vs LF and outer whitespace are transport noise, not semantics."""
    base = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "a\nb"}]
    )
    crlf = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "a\r\nb"}]
    )
    padded = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "  a\nb  "}]
    )
    assert base == crlf == padded
    # Interior whitespace stays significant (code blocks).
    indented = cache_key_for_request(
        tenant="t", model="mock", messages=[{"role": "user", "content": "a\n    b"}]
    )
    assert indented != base


def test_cache_key_v2_parity():
    """Pinned digest shared with the Rust edge test
    (gateway-rs cache_key_v2_parity_with_python). If this drifts on either
    side, edge HITs silently vanish."""
    key = cache_key_for_request(
        tenant="parity",
        model="mock",
        messages=[{"role": "user", "content": "  hello\r\nworld  "}],
        extras={
            "fetch_web_context": False,
            "web_query": None,
            "web_urls": [],
            "web_purpose": None,
            "web_format": None,
            "temperature": None,
            "max_tokens": None,
            "cache_control": None,
        },
    )
    assert key == (
        "at:parity:cache:v2:"
        "ea9e2e59350222baec8ed5fc7f85078ea788c48526f389bb6264ef251052db4d"
    )


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


def test_openai_compat_vendor_routing():
    from at_utility.providers import (
        OPENAI_COMPAT_VENDORS,
        MockProvider,
        build_compat_shells,
        compat_vendor_for_model,
        provider_key_available,
        resolve_provider,
    )

    mock = MockProvider()

    # Prefix → vendor mapping
    assert compat_vendor_for_model("gemini-3.1-pro") == "gemini"
    assert compat_vendor_for_model("deepseek-v4") == "deepseek"
    assert compat_vendor_for_model("kimi-k3") == "moonshot"
    assert compat_vendor_for_model("moonshot-v1-8k") == "moonshot"
    assert compat_vendor_for_model("glm-5.2") == "zai"
    assert compat_vendor_for_model("qwen3-max") == "qwen"
    assert compat_vendor_for_model("grok-4") == "xai"
    assert compat_vendor_for_model("gpt-4o-mini") is None
    assert compat_vendor_for_model("claude-3-5-sonnet-latest") is None

    class VendorSettings:
        deepseek_api_key = "sk-env-deepseek"

    compat = build_compat_shells(VendorSettings())
    assert set(compat) == {v for v, _p, _b in OPENAI_COMPAT_VENDORS}
    assert compat["deepseek"]._base_url == "https://api.deepseek.com/v1"
    assert compat["xai"]._base_url == "https://api.x.ai/v1"

    # BYOK routes to the vendor base URL with the customer key
    p, model = resolve_provider(
        "kimi-k3",
        openai=None,
        anthropic=None,
        mock=mock,
        fallback="mock",
        upstream_key="sk-customer-moonshot",
        allow_env_fallback=False,
        compat=compat,
    )
    assert model == "kimi-k3"
    assert p.name == "moonshot"
    assert p._api_key == "sk-customer-moonshot"  # type: ignore[attr-defined]
    assert p._base_url == "https://api.moonshot.ai/v1"  # type: ignore[attr-defined]

    # Env fallback only when the vendor shell has a key
    p, model = resolve_provider(
        "deepseek-v4",
        openai=None,
        anthropic=None,
        mock=mock,
        fallback="mock",
        upstream_key="",
        allow_env_fallback=True,
        compat=compat,
    )
    assert p.name == "deepseek"
    assert p._api_key == "sk-env-deepseek"  # type: ignore[attr-defined]

    # No key at all → mock (never leak to the wrong vendor)
    p, model = resolve_provider(
        "grok-4",
        openai=None,
        anthropic=None,
        mock=mock,
        fallback="mock",
        upstream_key="",
        allow_env_fallback=True,
        compat=compat,
    )
    assert p is mock and model == "mock"

    # provider_key_available honors per-vendor env keys
    assert provider_key_available(
        "deepseek-v4",
        upstream_key="",
        openai=None,
        anthropic=None,
        allow_env_fallback=True,
        compat=compat,
    )
    assert not provider_key_available(
        "gemini-3.1-pro",
        upstream_key="",
        openai=None,
        anthropic=None,
        allow_env_fallback=True,
        compat=compat,
    )


async def test_open_stream_with_retry_pre_first_byte():
    from at_utility.main import _open_stream_with_retry
    from at_utility.providers import ProviderUpstreamError

    class FlakyProvider:
        name = "flaky"

        def __init__(self, failures: int):
            self.failures = failures
            self.calls = 0

        async def chat_completion(self, *, model, messages, stream=True, **kwargs):
            self.calls += 1
            fail = self.calls <= self.failures

            async def gen():
                if fail:
                    raise ProviderUpstreamError(
                        "flaky", 503, {"error": {"message": "boom"}}
                    )
                yield 'data: {"choices":[]}\n\n'
                yield "data: [DONE]\n\n"

            return gen()

    # One pre-first-byte failure → retried once, stream proceeds
    p = FlakyProvider(failures=1)
    stream, first = await _open_stream_with_retry(
        p, model="m", messages=[], kwargs={}
    )
    assert p.calls == 2
    assert first is not None and first.startswith("data:")
    rest = [line async for line in stream]
    assert rest[-1] == "data: [DONE]\n\n"

    # Failure on both attempts → honest upstream error (no 200 error-frame stream)
    p2 = FlakyProvider(failures=2)
    try:
        await _open_stream_with_retry(p2, model="m", messages=[], kwargs={})
        raise AssertionError("expected ProviderUpstreamError")
    except ProviderUpstreamError as exc:
        assert exc.status_code == 503
    assert p2.calls == 2


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
