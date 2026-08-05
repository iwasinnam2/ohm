"""Unit tests for dual savings ledger."""

from at_utility.config import Settings
from at_utility.savings import dual_ledger, roi_ratio


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
