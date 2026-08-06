# Pricing

**BYOK ledgers:** You pay providers with your own keys. You pay **withOhm** for pipe rent — metered cache and web-fetch — with a **$0 Intermediate membership** (card on file). withOhm does not wholesale model tokens on Intermediate.

## Plans

See [/subscriptions](/subscriptions): **Intermediate (usage-led, $0 membership + meters, BYOK)** and Enterprise (design-partner rank). API/Stripe plan id for Intermediate is `payg`.

## Intermediate list rates (USD, rate card v2)

| Meter | Unit | List |
|-------|------|------|
| Cache hit | per 1k tokens | `$0.002` |
| Cache miss | per 1k tokens | `$0.001` |
| Web fetch | per URL | `$0.003` |

Hits are priced against the inference they replace (still ~90% below re-running the call); misses are priced low — they are pipe rent while your cache builds. A soft daily fetch cap applies until the first paid invoice unlocks the account (`AT_FREE_TIER_FETCH_CAP_DAY`).

## Commit tiers (optional)

Fixed monthly line for finance; metered usage included every cycle. Included usage applies to meters only (never the seat) and refreshes each billing cycle.

| Tier | Monthly | Included metered usage |
|------|---------|------------------------|
| `c29` | $29 | $35 |
| `c99` | $99 | $125 |
| `c499` | $499 | $700 |

Overage past the included amount bills at list rates. Pass `commit: "c29"` (or `c99`/`c499`) to `POST /v1/billing/checkout`, or pick a tier at [/subscriptions](/subscriptions).

## Invoice basis

Stripe invoices a **membership subscription** (typically `$0`) plus **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`). `/v1/usage` mirrors the same events (`invoice_basis: seat_plus_meters`) and reports `stripe_synced`.

| Event | Role |
|-------|------|
| **Membership** | Card on file; failed payment pauses web fetch (402) during Stripe retries, then suspends (403) after the dunning window or cancel |
| **Cache hit** | Redis replay rent (billable units = ceil(tokens/1000)) |
| **Cache miss** | Proxy fee (your provider still bills tokens) |
| **Web fetch** | Primary variable line — compliant URL ingest |

Live numbers: `GET /v1/enterprise/skus` and `GET /v1/usage`.

## Enterprise

**Contact us** — monthly dedicated / managed-capacity SKU with negotiated **transaction usage agreements** (fixed monthly for cache hits, misses, and web fetches). Design-partner rank includes weekly usage-budget reports, personal admin contact, and forum access. Contractual uptime SLA is published only under Enterprise agreements. Apply at [/billing/enterprise](/billing/enterprise).

## Self-serve

Start at [/billing/intermediate](/billing/intermediate) — Checkout issues your withOhm key once and collects a payment method. Meters invoice monthly. Enterprise applications: [/billing/enterprise](/billing/enterprise).

## Savings (estimates) — dual ledger

`GET /v1/savings` shows **estimated provider $ avoided** (blended list rate × cache-hit tokens), **pipe rent** (what withOhm metered), and **roi_ratio**. Always labeled estimate-only — not a guarantee. withOhm’s invoice and provider token bills stay separate.

## Org spend caps

Org policy may set monthly **pipe-rent** caps per cost center (`soft` response headers or `hard` HTTP 402). Caps are **not** Intermediate credits or prepaid balance — they gate MISS upstream flood; HITs still serve.
