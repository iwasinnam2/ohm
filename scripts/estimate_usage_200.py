#!/usr/bin/env python3
"""Estimate Intermediate meter revenue for a mixed 200-tenant cohort.

Rates come from the canonical rate card so the forecast can never drift
from what is actually charged.
"""

from __future__ import annotations

import json
from pathlib import Path

_CARD = json.loads(
    (Path(__file__).resolve().parents[1] / "pricing" / "rate_card.v2.json")
    .read_text(encoding="utf-8")
)
HIT = _CARD["meters"]["cache_hit"]["usd"]  # per 1k tokens
MISS = _CARD["meters"]["cache_miss"]["usd"]
FETCH = _CARD["meters"]["web_fetch"]["usd"]

COHORTS = [
    # name, count, tokens, hit_ratio, fetches
    ("indie", 120, 2_000_000, 0.55, 400),
    ("smb", 60, 12_000_000, 0.50, 5_000),
    ("larger", 20, 80_000_000, 0.45, 40_000),
]


def tenant_usd(tokens: int, hit_ratio: float, fetches: int) -> float:
    hit_tok = tokens * hit_ratio
    miss_tok = tokens - hit_tok
    return (hit_tok / 1000.0) * HIT + (miss_tok / 1000.0) * MISS + fetches * FETCH


def main() -> None:
    total = 0.0
    n = 0
    print("segment\tcount\tarpu_usd\tsubtotal_usd")
    for name, count, tokens, hit_r, fetches in COHORTS:
        arpu = tenant_usd(tokens, hit_r, fetches)
        sub = arpu * count
        total += sub
        n += count
        print(f"{name}\t{count}\t{arpu:.2f}\t{sub:.2f}")
    print(f"TOTAL\t{n}\t\t{total:.2f}")
    print(f"annualized_usd\t{total * 12:.2f}")


if __name__ == "__main__":
    main()
