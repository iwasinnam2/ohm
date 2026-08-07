"""Self-consistency: pricing/rate_card.v2.json is the canonical rate card.

The site imports the JSON directly; the Python config carries env-overridable
defaults. This test makes it impossible for the two to drift silently — a rate
change must go through the canonical file (by issuing a new version, per
docs/PRICING.md) and the config defaults together.
"""

from __future__ import annotations

import json
from pathlib import Path

from at_utility.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
RATE_CARD_PATH = REPO_ROOT / "pricing" / "rate_card.v2.json"


def _card() -> dict:
    return json.loads(RATE_CARD_PATH.read_text(encoding="utf-8"))


def _default_settings() -> Settings:
    # Bypass env so we compare code defaults, not the developer's .env.
    return Settings(_env_file=None)


def test_rate_card_exists_and_is_v2() -> None:
    card = _card()
    assert card["version"] == 2
    assert card["currency"] == "usd"


def test_meter_rates_match_config_defaults() -> None:
    card = _card()
    s = _default_settings()
    assert card["meters"]["cache_hit"]["usd"] == s.at_price_per_1k_tokens_hit
    assert card["meters"]["cache_miss"]["usd"] == s.at_price_per_1k_tokens_miss
    assert card["meters"]["web_fetch"]["usd"] == s.at_price_per_fetch


def test_meter_units_are_stable() -> None:
    card = _card()
    assert card["meters"]["cache_hit"]["unit"] == "per_1k_tokens"
    assert card["meters"]["cache_miss"]["unit"] == "per_1k_tokens"
    assert card["meters"]["web_fetch"]["unit"] == "per_url"


def test_commit_tiers_match_config_defaults() -> None:
    card = _card()
    s = _default_settings()
    tiers = {t["id"]: t for t in card["commit_tiers"]}
    assert set(tiers) == {"c29", "c99", "c499"}
    assert tiers["c29"]["included_usd"] == s.at_commit_included_usd_c29
    assert tiers["c99"]["included_usd"] == s.at_commit_included_usd_c99
    assert tiers["c499"]["included_usd"] == s.at_commit_included_usd_c499
    # Tier names encode their monthly price — keep them honest.
    for tier in tiers.values():
        assert tier["id"] == f"c{tier['usd_month']}"
        # Included usage must exceed the commit (the incentive to commit).
        assert tier["included_usd"] > tier["usd_month"]


def test_commit_ladder_is_coherent() -> None:
    """No rung more than ~5x the previous — no $29 -> $2,500 cliffs."""
    card = _card()
    rungs = sorted(t["usd_month"] for t in card["commit_tiers"])
    rungs.append(card["enterprise_from_usd_month"])
    for lower, upper in zip(rungs, rungs[1:]):
        assert upper / lower <= 5.1, f"ladder cliff: {lower} -> {upper}"


def test_enterprise_floor_matches_config() -> None:
    card = _card()
    s = _default_settings()
    assert card["enterprise_from_usd_month"] == s.at_enterprise_monthly_usd


def test_site_rate_card_copy_matches_canonical() -> None:
    """Amplify/Vercel only upload site/ — the committed mirror must stay equal."""
    site_copy = REPO_ROOT / "site" / "src" / "lib" / "rate_card.v2.json"
    assert site_copy.is_file(), "missing site/src/lib/rate_card.v2.json mirror"
    canonical = json.loads(RATE_CARD_PATH.read_text(encoding="utf-8"))
    mirrored = json.loads(site_copy.read_text(encoding="utf-8"))
    assert mirrored == canonical
