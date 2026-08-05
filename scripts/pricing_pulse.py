#!/usr/bin/env python3
"""Weekly pricing telemetry — feeds the pre-committed rules in docs/PRICING.md.

Pulls the last 7 days (override with PULSE_DAYS) from Stripe:
  - Checkout sessions created vs completed (the resistance signal)
  - New subscriptions by seat Price (tier mix)
  - Active subscription count + estimated committed MRR
  - Paid invoice volume (metered + seat revenue actually collected)

Read-only: needs a restricted key with read access to Checkout Sessions,
Subscriptions, Prices, and Invoices (STRIPE_SECRET_KEY / STRIPE_PULSE_KEY).
Output is a markdown summary on stdout (piped to the GitHub job summary by
.github/workflows/pricing-pulse.yml). Exit code stays 0 on partial data —
telemetry must never look like an outage.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import stripe

RATE_CARD = json.loads(
    (Path(__file__).resolve().parents[1] / "pricing" / "rate_card.v2.json")
    .read_text(encoding="utf-8")
)


def main() -> int:
    api_key = os.environ.get("STRIPE_PULSE_KEY") or os.environ.get(
        "STRIPE_SECRET_KEY", ""
    )
    if not api_key:
        print("pricing pulse: no STRIPE_PULSE_KEY/STRIPE_SECRET_KEY set", file=sys.stderr)
        print("## withOhm pricing pulse\n\n_No Stripe key configured — skipped._")
        return 0

    stripe.api_key = api_key
    days = int(os.environ.get("PULSE_DAYS", "7"))
    since = int(time.time()) - days * 86400

    lines: list[str] = [
        "## withOhm pricing pulse",
        "",
        f"Window: last {days} days · rate card v{RATE_CARD['version']} "
        f"(issued {RATE_CARD['issued']})",
        "",
    ]

    # --- Checkout funnel: created vs completed --------------------------------
    created = completed = 0
    by_commit: dict[str, int] = {}
    try:
        sessions = stripe.checkout.Session.list(
            created={"gte": since}, limit=100
        ).auto_paging_iter()
        for s in sessions:
            created += 1
            if s.get("status") == "complete":
                completed += 1
                tier = (s.get("metadata") or {}).get("commit_tier") or "metered"
                by_commit[tier] = by_commit.get(tier, 0) + 1
        rate = (completed / created * 100) if created else 0.0
        lines += [
            "### Checkout funnel",
            "",
            f"- Sessions created: **{created}**",
            f"- Sessions completed: **{completed}** ({rate:.0f}%)",
            f"- Completed by tier: {by_commit or '—'}",
            "",
            "Rules (docs/PRICING.md): <~25% over >=20 sessions -> step down a rung; "
            ">~60% with healthy retention -> draft v3 upward.",
            "",
        ]
    except Exception as exc:  # noqa: BLE001
        lines += [f"_Checkout funnel unavailable: {exc}_", ""]

    # --- Subscriptions: active count + committed MRR --------------------------
    try:
        active = 0
        mrr_cents = 0
        price_mix: dict[str, int] = {}
        subs = stripe.Subscription.list(status="active", limit=100).auto_paging_iter()
        for sub in subs:
            active += 1
            for item in sub.get("items", {}).get("data", []):
                price = item.get("price") or {}
                if price.get("recurring", {}).get("usage_type") == "metered":
                    continue
                nickname = price.get("nickname") or price.get("id", "?")
                price_mix[nickname] = price_mix.get(nickname, 0) + 1
                mrr_cents += int(price.get("unit_amount") or 0) * int(
                    item.get("quantity") or 1
                )
        lines += [
            "### Subscriptions",
            "",
            f"- Active subscriptions: **{active}**",
            f"- Committed MRR (seat lines only, metered excluded): "
            f"**${mrr_cents / 100:,.2f}**",
            f"- Seat price mix: {price_mix or '—'}",
            "",
        ]
    except Exception as exc:  # noqa: BLE001
        lines += [f"_Subscription data unavailable: {exc}_", ""]

    # --- Collected revenue: paid invoices in window ---------------------------
    try:
        paid_count = 0
        paid_cents = 0
        invoices = stripe.Invoice.list(
            status="paid", created={"gte": since}, limit=100
        ).auto_paging_iter()
        for inv in invoices:
            paid_count += 1
            paid_cents += int(inv.get("amount_paid") or 0)
        lines += [
            "### Collected",
            "",
            f"- Invoices paid: **{paid_count}**",
            f"- Amount collected: **${paid_cents / 100:,.2f}**",
            "",
        ]
    except Exception as exc:  # noqa: BLE001
        lines += [f"_Invoice data unavailable: {exc}_", ""]

    lines += [
        "---",
        "Decisions execute the pre-committed rules in docs/PRICING.md — "
        "not moods. Any change ships as rate card v3.",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
