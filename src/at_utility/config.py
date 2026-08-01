"""Env-driven configuration (adapted from forex-diamond-fsm config patterns)."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    at_api_keys: str = "sk-at-dev"
    at_region: str = "local"
    at_host: str = "0.0.0.0"
    at_port: int = 8080
    at_cache_ttl_seconds: int = 3600
    at_rate_limit_rps: float = 20.0
    at_rate_limit_burst: float = 40.0

    redis_url: str = "redis://127.0.0.1:6379/0"
    # Edge regions: REDIS_URL=local replica (GET), REDIS_WRITE_URL=leader (SET/meter)
    redis_write_url: str = ""
    # Regional token-bucket store (writable, colocated). Defaults to write URL.
    redis_rl_url: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    at_default_model: str = "mock"
    at_fallback_model: str = "mock"

    ingest_worker_url: str = "http://127.0.0.1:8090"
    playwright_timeout_ms: int = 30_000
    serp_provider: str = "duckduckgo"

    # Legal / compliance (docs/LEGAL.md) — default enforce UK+US public-only bounds
    at_compliance_enforce: bool = True
    at_compliance_require_ack: bool = True
    at_compliance_require_terms_ack: bool = True
    at_compliance_jurisdiction: str = "uk_us"  # uk | us_ca | uk_us | both
    at_compliance_respect_robots: bool = True
    at_compliance_redact_pii: bool = True
    at_compliance_max_chars_per_source: int = 4000
    at_compliance_max_context_chars: int = 12000
    at_compliance_allow_cache_training: bool = False
    at_compliance_terms_version: str = "tos-2026-07-26"
    at_compliance_dpa_version: str = "dpa-2026-07-26"
    at_compliance_user_agent: str = (
        "OhmBot/0.1 (+https://www.withohm.dev/docs/legal; public-retrieval; respect-robots)"
    )

    # Rate card v2 (pricing/rate_card.v2.json) — defaults asserted equal to the
    # canonical JSON by tests/test_rate_card.py. Env-overridable per deployment.
    at_price_per_1k_tokens_miss: float = 0.001
    at_price_per_1k_tokens_hit: float = 0.002
    at_price_per_fetch: float = 0.003
    # Blended provider list estimate for dual savings ledger ($/1k tokens).
    # Default $15/M ≈ mid-tier agent call (input+output avoided on full replay).
    # Override per deploy; always surfaced as estimate_only.
    at_provider_avoided_per_1k_tokens: float = 0.015
    at_enterprise_monthly_usd: float = 2500.0
    # When true, env OPENAI/ANTHROPIC keys may fill in if X-Ohm-Upstream-Key is
    # absent. Default OFF: silently burning operator keys for customer traffic
    # is a COGS leak. Enterprise/dev plans bypass this flag in main.py.
    at_byok_allow_env_fallback: bool = False
    # local | staging | production — production fails closed if meter Prices missing
    at_env: str = "local"
    # Soft daily web-fetch cap until invoice.paid / usage spend unlocks Intermediate
    at_free_tier_fetch_cap_day: int = 100
    # Days after first payment_failed before API hard-suspends (align with Stripe dunning window)
    at_delinquent_suspend_days: int = 14
    # Force meter Prices on Intermediate checkout even outside production
    at_require_meter_prices: bool = False

    # Shared secret for the Rust edge → /internal/edge-hit metering gate.
    # Empty disables edge HIT serving (edge falls back to full proxy).
    at_edge_shared_secret: str = ""

    at_admin_api_keys: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    # Recurring seat Price IDs ($0 Intermediate membership recommended)
    stripe_price_payg: str = ""
    stripe_price_enterprise: str = ""
    # Retired $29 credit pack (rate card v1) — kept only so in-flight webhooks
    # from old sessions can still resolve. New prepay is via commit tiers.
    stripe_price_credit_pack: str = ""
    # Commit tiers (rate card v2): licensed monthly seat Price IDs. Each cycle's
    # invoice.paid grants the included metered usage as a Stripe billing credit
    # scoped to metered prices (never offsets the seat fee itself).
    stripe_price_commit_c29: str = ""
    stripe_price_commit_c99: str = ""
    stripe_price_commit_c499: str = ""
    at_commit_included_usd_c29: float = 35.0
    at_commit_included_usd_c99: float = 125.0
    at_commit_included_usd_c499: float = 700.0
    # Stripe Tax: enable after activating Stripe Tax + origin address in the
    # dashboard (session creation fails if enabled without dashboard setup).
    stripe_automatic_tax: bool = False
    # Metered Prices attached to Billing Meters (required for Intermediate in production)
    stripe_price_meter_web_fetch: str = ""
    stripe_price_meter_cache_hit: str = ""
    stripe_price_meter_cache_miss: str = ""
    stripe_meter_event_web_fetch: str = "ohm_web_fetch"
    stripe_meter_event_cache_hit: str = "ohm_cache_hit"
    stripe_meter_event_cache_miss: str = "ohm_cache_miss"
    stripe_checkout_success_url: str = (
        "https://www.withohm.dev/billing/success?session_id={CHECKOUT_SESSION_ID}"
    )
    stripe_checkout_cancel_url: str = "https://www.withohm.dev/billing/cancel"
    # Design-partner defaults when plan=design_partner
    at_design_partner_days: int = 90
    at_design_partner_soft_quota_usd: float = 50.0
    at_design_partner_request_cap: int = 100_000

    # OIDC SSO (org console). Leave blank to use AT_SSO_DEV_SECRET for local.
    at_oidc_issuer: str = ""
    at_oidc_client_id: str = ""
    at_oidc_client_secret: str = ""
    at_oidc_authorize_url: str = ""
    at_oidc_token_url: str = ""
    at_oidc_userinfo_url: str = ""
    at_oidc_scopes: str = "openid profile email"
    at_oidc_redirect_uri: str = "https://www.withohm.dev/org/callback"
    at_oidc_allow_unverified_id_token: bool = False
    # Local/dev SSO shared secret (never set in production).
    at_sso_dev_secret: str = ""
    # Enterprise SKU delivery flags (catalog promises made real).
    at_enterprise_audit_logs: bool = True
    at_enterprise_managed_keys: bool = True
    at_enterprise_sla_note: str = (
        "Target 99.9% monthly API availability; credits negotiated per MSA. "
        "No contractual SLA until countersigned order form."
    )

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.at_api_keys.split(",") if k.strip()}

    @property
    def admin_api_key_set(self) -> set[str]:
        raw = self.at_admin_api_keys or self.at_api_keys
        return {k.strip() for k in raw.split(",") if k.strip()}

    def is_valid_api_key(self, key: str) -> bool:
        return key in self.api_key_set

    def is_admin_api_key(self, key: str) -> bool:
        return key in self.admin_api_key_set


@lru_cache
def get_settings() -> Settings:
    return Settings()
