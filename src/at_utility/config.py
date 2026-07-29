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
        "OhmBot/0.1 (+https://withohm.dev/legal; public-retrieval; respect-robots)"
    )

    at_price_per_1k_tokens_miss: float = 0.002
    at_price_per_1k_tokens_hit: float = 0.0005
    at_price_per_fetch: float = 0.001
    at_enterprise_monthly_usd: float = 2500.0
    # When true, env OPENAI/ANTHROPIC keys may fill in if X-Ohm-Upstream-Key is absent
    at_byok_allow_env_fallback: bool = True

    at_admin_api_keys: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    # Recurring seat Price IDs
    stripe_price_payg: str = ""
    stripe_price_enterprise: str = ""
    # Metered Prices attached to Billing Meters (optional until created in Dashboard)
    stripe_price_meter_web_fetch: str = ""
    stripe_price_meter_cache_hit: str = ""
    stripe_price_meter_cache_miss: str = ""
    stripe_meter_event_web_fetch: str = "ohm_web_fetch"
    stripe_meter_event_cache_hit: str = "ohm_cache_hit"
    stripe_meter_event_cache_miss: str = "ohm_cache_miss"
    stripe_checkout_success_url: str = (
        "https://withohm.dev/billing/success?session_id={CHECKOUT_SESSION_ID}"
    )
    stripe_checkout_cancel_url: str = "https://withohm.dev/billing/cancel"
    # Design-partner defaults when plan=design_partner
    at_design_partner_days: int = 90
    at_design_partner_soft_quota_usd: float = 50.0
    at_design_partner_request_cap: int = 100_000

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
