# Stripe webhook on public API (post-DNS)

After `https://api.withohm.dev/health` returns edge OK (not `edge_pending`):

## Endpoint (live)

| Field | Value |
|-------|--------|
| ID | `we_1TyTnNGdU0Iune6pCW8lkxjD` |
| URL | `https://api.withohm.dev/v1/billing/webhook` |
| Status | enabled (test mode) |
| Events | `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`, `invoice.marked_uncollectible` |

Signing secret → k8s / Secrets Manager `STRIPE_WEBHOOK_SECRET`.

## Catalog smoke (2026-07-29)

- Seat + all three meter Prices **active** (`STRIPE_PRICE_PAYG` + `STRIPE_PRICE_METER_*`)
- Public API: `external_smoke.ps1 -BaseUrl https://api.withohm.dev` **PASS** (mock miss/hit/usage)

## Dashboard (you — Revenue recovery)

API cannot set these; do once in [Dashboard](https://dashboard.stripe.com/acct_1TyM1fGdU0Iune6p/revenue_recovery/retries):

1. Smart Retries: **8 tries / 2 weeks**
2. Emails: **Send emails when card payments fail**
3. End action: **Cancel the subscription**
4. Optional: Customer Portal payment-method update link

Then full lifecycle: Intermediate Checkout (test card) → chat/fetch → `GET /v1/usage` `stripe_synced` → fail invoice / cancel → fetch 402 then 403. See [STRIPE_DUNNING.md](../../docs/STRIPE_DUNNING.md).

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-… -SkipOpenAI
```
