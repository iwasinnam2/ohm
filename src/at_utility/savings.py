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


def dual_ledger(
    *,
    hit_tokens: float,
    snap: dict[str, Any],
    settings: Settings,
) -> dict[str, Any]:
    """Fields shared by /v1/savings, receipts, and public aggregates."""
    hit_tok = float(hit_tokens)
    pipe_rent = float(snap.get("revenue_usd") or 0.0)
    provider = provider_avoided_usd(hit_tok, settings)
    pipe_proxy = pipe_proxy_avoided_usd(hit_tok, settings)
    ratio = roi_ratio(provider, pipe_rent)
    return {
        # Hero figure (backward-compatible field name): provider-scale estimate.
        "estimated_upstream_avoided_usd": provider,
        "estimated_provider_avoided_usd": provider,
        "estimated_pipe_proxy_avoided_usd": pipe_proxy,
        "pipe_rent_usd": pipe_rent,
        "roi_ratio": ratio,
        "provider_rate_per_1k_tokens": settings.at_provider_avoided_per_1k_tokens,
        "estimate_only": True,
    }


SAVINGS_DISCLAIMER = (
    "Dual ledger: estimated_provider_avoided_usd uses a blended provider "
    "list rate (AT_PROVIDER_AVOIDED_PER_1K_TOKENS) × cache-hit tokens; "
    "pipe_rent_usd is what Ohm metered. Estimates only — not a guaranteed "
    "savings promise. Ohm invoice ≠ provider pay-as-you-go."
)
