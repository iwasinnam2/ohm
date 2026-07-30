# How pricing works

**BYOK ledgers:** You pay OpenAI/Anthropic (and peers) with your own keys. You pay **withOhm** for pipe rent — metered cache and web-fetch — with a **$0 Intermediate membership** (card on file). Those are separate ledgers. withOhm does **not** wholesale model tokens on Intermediate.

Ingest (`fetch_web_context`) is always withOhm-owned and metered — the browse rocket.

## Invoice basis

| What Stripe invoices | What `/v1/usage` shows |
|----------------------|-------------------------|
| **$0 membership** + **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`) | Same events in Redis (ops source of truth) + estimates for savings UX |

`invoice_basis` on `/v1/usage`: `seat_plus_meters`.

## Seat + flow meters

| Event | Role | Default list (USD) |
|-------|------|--------------------|
| **Seat (Intermediate membership)** | Card on file; suspend→403 | `$0/mo` (`STRIPE_PRICE_PAYG`) |
| **Credit pack (optional)** | Prepaid meter allowance | `$29` (`STRIPE_PRICE_CREDIT_PACK`) |
| **Seat (Enterprise)** | Dedicated / managed-capacity SKU | `$2500/mo` (`STRIPE_PRICE_ENTERPRISE`) |
| **Cache hit** | Cheap Redis replay rent | `AT_PRICE_PER_1K_TOKENS_HIT` → meter `ohm_cache_hit` (qty = ceil(tokens/1000)) |
| **Cache miss** | Small proxy fee (not token wholesale) | `AT_PRICE_PER_1K_TOKENS_MISS` → meter `ohm_cache_miss` |
| **Web fetch** | **Primary variable revenue** | `AT_PRICE_PER_FETCH` → meter `ohm_web_fetch` |

Live catalog: `GET /v1/enterprise/skus`. Meter snapshot: `GET /v1/usage`.

## Enterprise managed pool

Monthly dedicated pool SKU (`enterprise-dedicated-pool`): Ohm-held provider keys, connection pools, single-tenant Redis option, regional quota reservation, audit logs. No contractual uptime SLA until a signed schedule (`sla: null`). This is where managed keys win the rate-limit job.

## Design partners

Complimentary `design_partner` plan (admin issue): time-boxed + soft USD quota. No Stripe required. See [DESIGN_PARTNERS.md](DESIGN_PARTNERS.md).

## Stripe

- **Self-serve:** `POST /v1/billing/checkout` (site `/billing/intermediate`) — issues withOhm key once + Checkout URL ($0 membership + meters)
- **Ops:** `POST /v1/admin/tenants/{id}/checkout`
- Cancel / payment failed → tenant `suspended` → API keys return **403**
- Soft daily fetch cap until `invoice.paid` / metered spend — see [STRIPE.md](STRIPE.md)
- Success / cancel pages: `https://www.withohm.dev/billing/success` / `cancel`
- Setup: [STRIPE.md](STRIPE.md)
- Intermediate UI label ↔ API/Stripe plan id `payg`

## Savings (estimates)

`GET /v1/usage` and `GET /v1/savings` expose **estimated** upstream cost avoided from identical-request cache hits. Not guaranteed savings. Ohm’s invoice ≠ provider token bills.
