# Pricing

**BYOK ledgers:** You pay providers with your own keys. You pay **withOhm** for pipe access (seat) plus metered cache and web-fetch rent. withOhm does not wholesale model tokens on pay-as-you-go Intermediate plans.

## Plans

See [/subscriptions](/subscriptions) for Free trial, Intermediate ($29/mo), and Enterprise (design-partner rank).

## Invoice basis

Stripe invoices a **monthly subscription seat** plus **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`). `/v1/usage` mirrors the same events (`invoice_basis: seat_plus_meters`).

| Event | Role |
|-------|------|
| **Seat** | Right to use the withOhm pipe — suspend→403 if unpaid |
| **Cache hit** | Redis replay rent |
| **Cache miss** | Proxy fee (your provider still bills tokens) |
| **Web fetch** | Primary variable line — compliant URL ingest |

Live numbers: `GET /v1/enterprise/skus` and `GET /v1/usage`.

## Enterprise

Monthly dedicated / managed-capacity SKU with negotiated **transaction usage agreements** (fixed monthly for cache hits, misses, and web fetches). Design-partner rank includes weekly usage-budget reports, personal admin contact, and forum access. Contractual uptime SLA is published only under Enterprise agreements.

## Self-serve

Start at [/billing/intermediate](/billing/intermediate) — Checkout issues your withOhm key once, then Stripe collects the seat. Free trial requires payment details and a $0.01 verification charge; Intermediate billing begins after 30 days. Enterprise applications: [/billing/enterprise](/billing/enterprise).

## Savings (estimates)

`GET /v1/usage` and `GET /v1/savings` expose **estimated** upstream cost avoided from cache hits — not guaranteed savings. withOhm’s invoice and provider token bills stay separate.
