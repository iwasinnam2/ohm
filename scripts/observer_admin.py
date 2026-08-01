#!/usr/bin/env python3
"""Monthly business-admin digest — tax, invoices, payouts as tickets, not memory.

Runs on the 1st of each month (observer-admin.yml) over the previous calendar
month of Stripe data:
  - Paid invoices: count, gross collected, tax collected (Stripe Tax)
  - Payouts to the bank: count + total
  - Refunds and open disputes (each one is admin work)

The digest goes to Slack and a Linear reconciliation task is opened so the
tax/invoice/admin cadence exists as a trackable ticket. Read-only Stripe key
(STRIPE_PULSE_KEY); exits 0 on partial data — a reporting gap must not look
like an outage.
"""

from __future__ import annotations

import calendar
import os
import sys
from datetime import datetime, timezone

import stripe

from observer_notify import notify


def month_window(now: datetime) -> tuple[int, int, str]:
    """Previous calendar month as (start_ts, end_ts, label)."""
    year, month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = calendar.monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    return int(start.timestamp()), int(end.timestamp()), start.strftime("%B %Y")


def main() -> int:
    api_key = os.environ.get("STRIPE_PULSE_KEY") or os.environ.get(
        "STRIPE_SECRET_KEY", ""
    )
    if not api_key:
        print("observer-admin: no Stripe key configured — skipped", file=sys.stderr)
        print("_No Stripe key configured — digest skipped._")
        return 0

    stripe.api_key = api_key
    since, until, label = month_window(datetime.now(timezone.utc))
    window = {"gte": since, "lte": until}
    lines: list[str] = [f"Monthly admin digest — {label}", ""]

    try:
        count = gross = tax = 0
        for inv in stripe.Invoice.list(
            status="paid", created=window, limit=100
        ).auto_paging_iter():
            count += 1
            gross += int(inv.get("amount_paid") or 0)
            tax += int(inv.get("tax") or 0)
        lines += [
            f"Invoices paid: {count}",
            f"Gross collected: ${gross / 100:,.2f}",
            f"Tax collected (Stripe Tax): ${tax / 100:,.2f}",
            "",
        ]
    except Exception as exc:  # noqa: BLE001
        lines += [f"Invoice data unavailable: {exc}", ""]

    try:
        pcount = ptotal = 0
        for payout in stripe.Payout.list(created=window, limit=100).auto_paging_iter():
            pcount += 1
            ptotal += int(payout.get("amount") or 0)
        lines += [f"Payouts: {pcount} totalling ${ptotal / 100:,.2f}", ""]
    except Exception as exc:  # noqa: BLE001
        lines += [f"Payout data unavailable: {exc}", ""]

    try:
        rcount = rtotal = 0
        for refund in stripe.Refund.list(created=window, limit=100).auto_paging_iter():
            rcount += 1
            rtotal += int(refund.get("amount") or 0)
        disputes = [
            d
            for d in stripe.Dispute.list(limit=100).auto_paging_iter()
            if d.get("status") not in ("won", "lost", "charge_refunded")
        ]
        lines += [
            f"Refunds: {rcount} totalling ${rtotal / 100:,.2f}",
            f"Open disputes: {len(disputes)}"
            + (" — HANDLE THESE FIRST" if disputes else ""),
            "",
        ]
    except Exception as exc:  # noqa: BLE001
        lines += [f"Refund/dispute data unavailable: {exc}", ""]

    lines += [
        "Checklist: reconcile payouts against the bank, file/forward VAT "
        "records, archive invoices, review dunning (delinquent tenants), "
        "close this ticket when done.",
    ]

    body = "\n".join(lines)
    print(body)
    notify(f"reconcile: {label} (tax, invoices, payouts)", body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
