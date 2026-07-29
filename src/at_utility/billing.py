"""Billing helpers for cache-arbitrage margin reporting."""

from __future__ import annotations

from typing import Any


def arbitrage_summary(usage: dict[str, Any]) -> dict[str, Any]:
    """
    On cache hits, COGS ≈ 0 and billed_hit ≈ revenue.
    Misses carry downstream provider cost (not modeled here beyond list price).
    """
    hit_usd = float(usage.get("cache_hit_usd") or 0)
    miss_usd = float(usage.get("cache_miss_usd") or 0)
    fetch_usd = float(usage.get("fetch_usd") or 0)
    revenue = hit_usd + miss_usd + fetch_usd
    # Treat hit revenue as near-pure margin for dashboarding
    estimated_margin = hit_usd + fetch_usd * 0.3
    return {
        "revenue_usd": revenue,
        "estimated_high_margin_usd": estimated_margin,
        "cache_hit_share": (
            hit_usd / revenue if revenue > 0 else 0.0
        ),
        "enterprise_upsell_usd": float(usage.get("enterprise_monthly_usd") or 0),
    }
