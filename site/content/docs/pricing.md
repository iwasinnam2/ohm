# Pricing

**BYOK ledgers:** You pay providers with your own keys. You pay **Ohm** for pipe access (seat) plus metered cache and web-fetch rent. Ohm does not wholesale model tokens on PAYG.

## Invoice basis

Stripe invoices a **monthly subscription seat** plus **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`). `/v1/usage` mirrors the same events (`invoice_basis: seat_plus_meters`).

| Event | Role |
|-------|------|
| **Seat** | Right to use the Ohm pipe — suspend→403 if unpaid |
| **Cache hit** | Cheap Redis replay rent |
| **Cache miss** | Small proxy fee (your provider still bills tokens) |
| **Web fetch** | Primary variable line — compliant URL ingest |

Live numbers: `GET /v1/enterprise/skus` and `GET /v1/usage`.

## Enterprise

Monthly dedicated / managed-capacity SKU: Ohm-held keys and reserved pools. No published contractual uptime SLA for MVP.

## Self-serve

Start at [/billing](/billing) — Checkout issues your Ohm key once, then Stripe collects the seat. Ops escape hatch: admin checkout on an existing tenant.

## Design partners

Complimentary time-boxed keys (`plan=design_partner`) — see [design partners](/design-partners).

## Savings (estimates)

`GET /v1/usage` and `GET /v1/savings` expose **estimated** upstream cost avoided from cache hits — not guaranteed savings. Ohm’s invoice and provider token bills stay separate.
