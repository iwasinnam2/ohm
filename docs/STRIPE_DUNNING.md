# Stripe dunning + payment enforcement (withOhm)

## How Stripe delayed / failed invoice collection works

Subscription meter invoices use **automatic collection** (`charge_automatically`) against the card collected at Intermediate Checkout.

1. Stripe finalizes the monthly invoice (seat `$0` + metered usage).
2. If the charge fails, Stripe emits `invoice.payment_failed` and schedules **Smart Retries** (Dashboard → Billing → Revenue recovery → Retries). Recommended: **8 attempts within 2 weeks**.
3. On each failed attempt, Stripe can email the customer (**Send emails when card payments fail**) with a link to update the payment method.
4. For `send_invoice` collection, enable **Send reminders if a recurring invoice hasn’t been paid** and add a schedule (before / on / after due).
5. After the retry window, configure the end action to **Cancel the subscription** or **Mark as unpaid** — withOhm then hard-suspends the API key (HTTP 403).

withOhm does **not** suspend on the first `invoice.payment_failed`. That would kill the reminder window. Instead:

| Day (from first failure) | Stripe | withOhm API |
|--------------------------|--------|-------------|
| 0 | `invoice.payment_failed`; Smart Retry queued | `billing_paid=false`, `billing_delinquent_since` set; **web fetch blocked** (402); chat still works |
| 1–13 | Retries + failed-payment emails (urgency rises with each failure email) | Same soft lock; meters still record any remaining chat usage for the next invoice |
| ≥14 (`AT_DELINQUENT_SUSPEND_DAYS`) | End of retry schedule / cancel / unpaid | **Suspended** → all API calls **403** |
| Anytime `invoice.paid` | Recovered | Delinquency cleared; fetch unlocks |

Also suspend immediately on: `customer.subscription.deleted`, `invoice.marked_uncollectible`, subscription status `canceled` / `unpaid` / `incomplete_expired`.

## Dashboard checklist (do this once)

1. **[Revenue recovery → Retries](https://dashboard.stripe.com/revenue_recovery/retries):** Smart Retries, **8 tries / 2 weeks** (Stripe default recommendation; covers days 1–14).
2. **[Revenue recovery → Emails](https://dashboard.stripe.com/revenue_recovery/emails):** enable **Send emails when card payments fail** (email after **each** failed attempt, with payment-method update link).
3. **[Subscriptions and emails](https://dashboard.stripe.com/settings/billing/automatic):** link destination = Stripe Customer Portal (or your `/billing/intermediate` page).
4. **End action after retries:** **Cancel the subscription** (fires `customer.subscription.deleted` → withOhm hard-suspend). Avoid “leave past_due” — that lets usage continue indefinitely.
5. Optional: [Billing Automations](https://docs.stripe.com/billing/automations) for custom segments (Enterprise vs Intermediate).

### Escalating urgency schedule (days 1–14)

Stripe’s failed-payment emails fire on **each** Smart Retry — that alone escalates over two weeks. For explicit copy tiers (recommended ops setup):

| Window | Channel | Tone |
|--------|---------|------|
| Day 0–1 | Stripe failed-payment email #1 | Soft: “Payment didn’t go through — update card” |
| Day 3–4 | Stripe retry email #2–3 | Firm: “Still unpaid — retries continuing” |
| Day 7 | Automation or Resend (optional) | Urgent: “Web fetch already paused; API suspends in 7 days” |
| Day 10–12 | Stripe retry emails | Final: “Last retries before cancel” |
| Day 14 | Cancel sub + withOhm suspend | Hard stop: API **403** |

For `send_invoice` (Enterprise wire / NET terms): enable **Send reminders if a recurring invoice hasn’t been paid** and add reminders **on due**, **+3 days**, **+7 days**, **+14 days**. After the window, mark uncollectible → withOhm suspends on `invoice.marked_uncollectible`.

Refs: [Smart Retries](https://docs.stripe.com/billing/revenue-recovery/smart-retries), [Customer emails](https://docs.stripe.com/billing/revenue-recovery/customer-emails), [Automatic collection](https://docs.stripe.com/invoicing/automatic-collection).

## Metering cannot be sidestepped

- Checkout in production **requires** all three meter Prices (`AT_ENV=production` / `AT_REQUIRE_METER_PRICES`).
- Usage is written to Redis **and** Stripe `MeterEvent` when `stripe_customer_id` is set.
- Delinquent tenants cannot use the revenue rocket (web fetch) until paid.
- After 14 days unpaid, keys are dead (403) — no silent free pipe.

## Webhooks to forward

```
checkout.session.completed
invoice.paid
invoice.payment_failed
invoice.marked_uncollectible
customer.subscription.updated
customer.subscription.deleted
```

```bash
stripe listen --forward-to localhost:8080/v1/billing/webhook \
  --events checkout.session.completed,invoice.paid,invoice.payment_failed,invoice.marked_uncollectible,customer.subscription.updated,customer.subscription.deleted
```
