"""Dual savings ledger — pipe rent vs estimated provider spend avoided.

Provider avoidance is an *estimate* from a configurable blended list rate
(AT_PROVIDER_AVOIDED_PER_1K_TOKENS). It is not a guarantee and is always
surfaced with estimate_only=true.
"""

from __future__ import annotations

from typing import Any

from at_utility.config import Settings


def provider_avoided_usd(hit_tokens: float, settings: Settings) -> float:
    """Counterfactual: hit tokens billed at blended provider list rate."""
    return (float(hit_tokens) / 1000.0) * float(
        settings.at_provider_avoided_per_1k_tokens
    )


def pipe_proxy_avoided_usd(hit_tokens: float, settings: Settings) -> float:
    """Legacy counterfactual: hits priced as Ohm miss rent (understates labs)."""
    return (float(hit_tokens) / 1000.0) * float(
        settings.at_price_per_1k_tokens_miss
    )


def roi_ratio(provider_avoided: float, pipe_rent: float) -> float | None:
    """Estimated provider $ avoided per $1 of Ohm pipe rent."""
    if pipe_rent <= 0:
        return None
    return float(provider_avoided) / float(pipe_rent)


def provider_cache_read_savings_usd(cache_read_tokens: float, settings: Settings) -> float:
    """Estimated $ saved because the upstream *provider's own* prompt cache
    (docs/CACHE_AUTOPILOT.md) served `cache_read_tokens` at a discount,
    instead of Ohm's own exact-replay cache skipping the call entirely.

    Distinct rail from `provider_avoided_usd`: this fires on Ohm MISSes too
    — Ohm still made the call, but the breakpoint autopilot (or a
    cache-aware client) got the provider to discount part of it.
    """
    return (
        (float(cache_read_tokens) / 1000.0)
        * float(settings.at_provider_avoided_per_1k_tokens)
        * float(settings.at_provider_cache_discount_pct)
    )


def dual_ledger(
    *,
    hit_tokens: float,
    snap: dict[str, Any],
    settings: Settings,
    upstream_cache_read_tokens: float = 0.0,
    upstream_cache_creation_tokens: float = 0.0,
) -> dict[str, Any]:
    """Fields shared by /v1/savings, receipts, and public aggregates.

    Three independent rails, never summed into one number:
      1. estimated_provider_avoided_usd — Ohm's own exact-replay HITs
         (`hit_tokens`): the call never happened at all.
      2. estimated_pipe_proxy_avoided_usd — legacy conservative variant of (1).
      3. estimated_provider_cache_savings_usd — the provider's *own* prompt
         cache discounting part of an Ohm MISS (breakpoint autopilot /
         cache-aware clients). The call still happened; only part of its
         cost was discounted upstream.
    """
    hit_tok = float(hit_tokens)
    pipe_rent = float(snap.get("revenue_usd") or 0.0)
    provider = provider_avoided_usd(hit_tok, settings)
    pipe_proxy = pipe_proxy_avoided_usd(hit_tok, settings)
    ratio = roi_ratio(provider, pipe_rent)
    cache_read = float(upstream_cache_read_tokens)
    cache_creation = float(upstream_cache_creation_tokens)
    cache_denom = cache_read + cache_creation
    provider_cache_savings = provider_cache_read_savings_usd(cache_read, settings)
    return {
        # Hero figure (backward-compatible field name): provider-scale estimate.
        "estimated_upstream_avoided_usd": provider,
        "estimated_provider_avoided_usd": provider,
        "estimated_pipe_proxy_avoided_usd": pipe_proxy,
        "pipe_rent_usd": pipe_rent,
        "roi_ratio": ratio,
        "provider_rate_per_1k_tokens": settings.at_provider_avoided_per_1k_tokens,
        # Third rail (docs/CACHE_AUTOPILOT.md) — provider's own cache, not Ohm's.
        "provider_cache_read_tokens": cache_read,
        "provider_cache_creation_tokens": cache_creation,
        "provider_cache_hit_ratio": (cache_read / cache_denom) if cache_denom > 0 else 0.0,
        "estimated_provider_cache_savings_usd": provider_cache_savings,
        "provider_cache_discount_pct": settings.at_provider_cache_discount_pct,
        "estimate_only": True,
    }


SAVINGS_DISCLAIMER = (
    "Triple ledger: estimated_provider_avoided_usd uses a blended provider "
    "list rate (AT_PROVIDER_AVOIDED_PER_1K_TOKENS) × cache-hit tokens; "
    "estimated_provider_cache_savings_usd applies the same rate at "
    "AT_PROVIDER_CACHE_DISCOUNT_PCT to upstream provider-cache-read tokens "
    "(breakpoint autopilot, docs/CACHE_AUTOPILOT.md) — a different mechanism, "
    "never summed with the first; pipe_rent_usd is what Ohm metered. "
    "Estimates only — not a guaranteed savings promise. "
    "Ohm invoice ≠ provider pay-as-you-go."
)
