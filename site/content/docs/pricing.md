# Pricing

**BYOK ledgers:** You pay providers with your own keys. You pay **withOhm** for pipe rent — metered cache and web-fetch — with a **$0 Intermediate membership** (card on file). withOhm does not wholesale model tokens on Intermediate.

## Plans

See [/subscriptions](/subscriptions): **Intermediate (usage-led, $0 membership + meters, BYOK)** and Enterprise (design-partner rank). API/Stripe plan id for Intermediate is `payg`.

## Intermediate list rates (USD)

| Meter | Unit | List |
|-------|------|------|
| Cache hit | per 1k tokens | `$0.0005` |
| Cache miss | per 1k tokens | `$0.002` |
| Web fetch | per URL | `$0.001` |

Optional **$29 meter credit pack** prepaid toward usage — not a required seat. Soft daily fetch cap applies until the first paid invoice / metered spend unlocks the account (`AT_FREE_TIER_FETCH_CAP_DAY`).

## Invoice basis

Stripe invoices a **membership subscription** (typically `$0`) plus **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`). `/v1/usage` mirrors the same events (`invoice_basis: seat_plus_meters`) and reports `stripe_synced`.

| Event | Role |
|-------|------|
| **Membership** | Card on file; suspend→403 if unpaid / cancelled |
| **Cache hit** | Redis replay rent (billable units = ceil(tokens/1000)) |
| **Cache miss** | Proxy fee (your provider still bills tokens) |
| **Web fetch** | Primary variable line — compliant URL ingest |

Live numbers: `GET /v1/enterprise/skus` and `GET /v1/usage`.

## Enterprise

Monthly dedicated / managed-capacity SKU with negotiated **transaction usage agreements** (fixed monthly for cache hits, misses, and web fetches). Design-partner rank includes weekly usage-budget reports, personal admin contact, and forum access. Contractual uptime SLA is published only under Enterprise agreements.

## Self-serve

Start at [/billing/intermediate](/billing/intermediate) — Checkout issues your withOhm key once and collects a payment method. Meters invoice monthly. Enterprise applications: [/billing/enterprise](/billing/enterprise).

## Savings (estimates)

`GET /v1/usage` and `GET /v1/savings` expose **estimated** upstream cost avoided from cache hits — not guaranteed savings. withOhm’s invoice and provider token bills stay separate.
