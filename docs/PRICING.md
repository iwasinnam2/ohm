# How pricing works

**BYOK ledgers:** You pay OpenAI/Anthropic (and peers) with your own keys. You pay **withOhm** for pipe rent — metered cache and web-fetch — with a **$0 Intermediate membership** (card on file). Those are separate ledgers. withOhm does **not** wholesale model tokens on Intermediate.

Ingest (`fetch_web_context`) is always withOhm-owned and metered — the browse rocket.

## Rate card v2 — canonical source and anchors

The canonical rate card is [pricing/rate_card.v2.json](../pricing/rate_card.v2.json). The site imports it directly; Python config defaults are asserted equal by `tests/test_rate_card.py`. **Never edit rates in place — issue a new version.** Stripe Prices are immutable; existing subscriptions grandfather automatically.

| Meter | v2 list (USD) | External anchor (2026) |
|-------|---------------|------------------------|
| Cache hit | `$0.002` / 1k tokens | Provider cache reads are ~10% of input ($0.30–0.50/M) and still charge full output ($15–30/M). A hit replaces the whole call; $2/M captures ~10–20% of avoided spend. |
| Cache miss | `$0.001` / 1k tokens | OpenRouter's BYOK take is ~5% of inference (~$0.25/M blended). The miss meter is the visible per-call tax — the real price-resistance point — so it is priced low. |
| Web fetch | `$0.003` / URL | Tavily PAYG $0.008/credit; Firecrawl Hobby $0.0032/page with no PAYG option. $3/1k undercuts Tavily 62% with the compliance pipe included. |

**Commit tiers** (fixed monthly line; included metered usage refreshes each cycle, scoped to meters only, never the seat): `c29` $29/mo → $35 included · `c99` $99/mo → $125 · `c499` $499/mo → $700. Ladder rungs stay within ~5x of each other up to Enterprise ($2,500/mo).

## Pre-committed adjustment rules (no moods, no ego)

Decided at v2 issue time (2026-07-31), executed on data from the weekly pricing pulse (`.github/workflows/pricing-pulse.yml`):

1. **Review checkpoint:** 30 days after the first live checkout, then monthly.
2. **Resistance trigger:** checkout-started → paid conversion below **~25%** across ≥20 sessions → step the offending surface down one rung (commit tier price or the fetch meter — never the miss meter, it is already floor-priced).
3. **Underpricing trigger:** conversion above **~60%** with month-2 retention ≥80% → draft rate card v3 upward (hit and fetch first — they are the value events).
4. **Tier-mix signal:** if >50% of commits land on the top tier, add a higher rung; if >80% land on the bottom, the ladder is too steep.
5. **Any change ships as v3**: new JSON version, new Stripe Prices, config defaults, one commit. Existing subscribers keep v2 prices unless they re-checkout.

## Invoice basis

| What Stripe invoices | What `/v1/usage` shows |
|----------------------|-------------------------|
| **$0 membership** + **Billing Meter** usage (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`) | Same events in Redis (ops source of truth) + estimates for savings UX |

`invoice_basis` on `/v1/usage`: `seat_plus_meters`.

## Seat + flow meters

| Event | Role | Default list (USD) |
|-------|------|--------------------|
| **Seat (Intermediate membership)** | Card on file; suspend→403 | `$0/mo` (`STRIPE_PRICE_PAYG`) |
| **Commit tiers** | Fixed monthly seat + included metered usage per cycle (billing credit scoped to meters) | `c29/c99/c499` (`STRIPE_PRICE_COMMIT_*`) |
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
- Payment failed → delinquent: web fetch returns **402** while Stripe Smart Retries run (1–14 days); after `AT_DELINQUENT_SUSPEND_DAYS` or cancel → tenant `suspended` → **403** ([STRIPE_DUNNING.md](STRIPE_DUNNING.md))
- Soft daily fetch cap until `invoice.paid` — metered spend alone never unlocks; see [STRIPE.md](STRIPE.md)
- Success / cancel pages: `https://www.withohm.dev/billing/success` / `cancel`
- Setup: [STRIPE.md](STRIPE.md)
- Intermediate UI label ↔ API/Stripe plan id `payg`

## Savings (estimates) — dual ledger

`GET /v1/savings` (and receipts / `ohm_savings`) expose a **dual ledger**:

| Field | Meaning |
|-------|---------|
| `estimated_provider_avoided_usd` | Cache-hit tokens × `AT_PROVIDER_AVOIDED_PER_1K_TOKENS` (default **$0.015/1k** = $15/M blended list estimate) |
| `pipe_rent_usd` | Ohm metered revenue (hits + misses + fetches) |
| `roi_ratio` | Provider avoided ÷ pipe rent |
| `estimated_pipe_proxy_avoided_usd` | Legacy counterfactual at Ohm miss rent (understates labs) |

`estimated_upstream_avoided_usd` aliases the provider figure. Always
`estimate_only: true`. Not guaranteed savings. Ohm’s invoice ≠ provider token bills.
See [GEM_POSITION.md](GEM_POSITION.md). Enterprise governance (SSO, ledger,
org policy): [ENTERPRISE.md](ENTERPRISE.md) · [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).
