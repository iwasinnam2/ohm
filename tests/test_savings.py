"""Unit tests for dual savings ledger."""

import pytest

from at_utility.config import Settings
from at_utility.savings import dual_ledger, provider_cache_read_savings_usd, roi_ratio


def test_dual_ledger_provider_gt_pipe_proxy():
    settings = Settings(
        at_price_per_1k_tokens_miss=0.001,
        at_provider_avoided_per_1k_tokens=0.015,
    )
    ledger = dual_ledger(
        hit_tokens=1000.0,
        snap={"revenue_usd": 0.5},
        settings=settings,
    )
    assert ledger["estimated_provider_avoided_usd"] == 0.015
    assert ledger["estimated_upstream_avoided_usd"] == 0.015
    assert ledger["estimated_pipe_proxy_avoided_usd"] == 0.001
    assert ledger["pipe_rent_usd"] == 0.5
    assert ledger["roi_ratio"] == 0.03
    assert ledger["estimate_only"] is True


def test_roi_ratio_none_when_no_rent():
    assert roi_ratio(10.0, 0.0) is None


def test_provider_cache_read_savings_usd():
    settings = Settings(
        at_provider_avoided_per_1k_tokens=0.015, at_provider_cache_discount_pct=0.9
    )
    assert provider_cache_read_savings_usd(1000.0, settings) == pytest.approx(
        0.015 * 0.9
    )


def test_dual_ledger_third_rail_defaults_to_zero_and_is_backward_compatible():
    """No upstream cache tokens passed → third rail is present but zero, and
    the original two-rail fields are byte-identical to before this rail
    existed."""
    settings = Settings(
        at_price_per_1k_tokens_miss=0.001,
        at_provider_avoided_per_1k_tokens=0.015,
    )
    ledger = dual_ledger(hit_tokens=1000.0, snap={"revenue_usd": 0.5}, settings=settings)
    assert ledger["estimated_provider_avoided_usd"] == 0.015
    assert ledger["estimated_pipe_proxy_avoided_usd"] == 0.001
    assert ledger["provider_cache_read_tokens"] == 0.0
    assert ledger["provider_cache_creation_tokens"] == 0.0
    assert ledger["provider_cache_hit_ratio"] == 0.0
    assert ledger["estimated_provider_cache_savings_usd"] == 0.0


def test_dual_ledger_third_rail_with_upstream_cache_tokens():
    settings = Settings(
        at_provider_avoided_per_1k_tokens=0.015, at_provider_cache_discount_pct=0.9
    )
    ledger = dual_ledger(
        hit_tokens=0.0,
        snap={"revenue_usd": 1.0},
        settings=settings,
        upstream_cache_read_tokens=1800.0,
        upstream_cache_creation_tokens=200.0,
    )
    assert ledger["provider_cache_read_tokens"] == 1800.0
    assert ledger["provider_cache_creation_tokens"] == 200.0
    assert ledger["provider_cache_hit_ratio"] == pytest.approx(0.9)
    assert ledger["estimated_provider_cache_savings_usd"] == pytest.approx(
        (1800.0 / 1000.0) * 0.015 * 0.9
    )
    # Independent of, and never summed with, Ohm's own exact-replay rail.
    assert ledger["estimated_provider_avoided_usd"] == 0.0
