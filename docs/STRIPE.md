# Stripe (withOhm)

## Billing model

| Layer | Behavior |
|-------|----------|
| **Membership seat** | Monthly subscription via Checkout (`mode=subscription`, qty 1). Intermediate default is **$0** (card on file). |
| **Meters** | Stripe Billing Meters: `ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss` — events synced from Redis metering |
| **Commit tiers (optional)** | `c29/c99/c499` fixed monthly seats (`STRIPE_PRICE_COMMIT_*`) — each cycle's `invoice.paid` grants the included metered usage as a Billing Credit Grant scoped to metered prices (never offsets the seat). Old `/v1/billing/topup` returns **410**. |
| **Dunning (1–14d)** | First `invoice.payment_failed` → delinquent (fetch **402**); Stripe Smart Retries + emails; day ≥`AT_DELINQUENT_SUSPEND_DAYS` → **403**. See [STRIPE_DUNNING.md](STRIPE_DUNNING.md) |
| **Suspend** | `customer.subscription.deleted` / `invoice.marked_uncollectible` / sub `canceled`\|`unpaid` → tenant `suspended` → **403** |
| **Fetch soft-cap** | `AT_FREE_TIER_FETCH_CAP_DAY` (default 100) until `invoice.paid` unlocks Intermediate — metered spend alone never unlocks |
| **Meter DLQ** | Failed meter events queue in Redis (`at:global:stripe_meter_dlq`) and replay every 60s; identifier dedup keeps replays single-billed |

Checkout **line items are seat-only** (membership or commit tier) so hosted
Checkout does not list hit/miss/fetch as charges. Meter Prices are still
required when `AT_ENV=production` or `AT_REQUIRE_METER_PRICES=true`; they are
attached to the subscription on `checkout.session.completed`
(`attach_meter_prices_to_subscription`). Rates are printed as fine print on
the Intermediate billing page.

Self-serve flow: `POST /v1/billing/checkout` creates a **pending** signup (no
API key yet) → Stripe → `checkout.session.completed` / `claim-key` issues the
first secret once. Further keys: `GET|POST|DELETE /v1/account/keys` with any
active Bearer on that Stripe customer (no re-checkout).

### Meter units (must match Prices)

| Event | Stripe quantity | List USD (`AT_PRICE_*`) |
|-------|-----------------|-------------------------|
| `ohm_cache_hit` | `ceil(tokens/1000)` — zero tokens bill zero units | `$0.002` / 1k tokens |
| `ohm_cache_miss` | `ceil(tokens/1000)` — zero tokens bill zero units | `$0.001` / 1k tokens |
| `ohm_web_fetch` | URL count | `$0.003` / URL |

Rates are governed by [PRICING.md](PRICING.md) and the canonical [pricing/rate_card.v2.json](../pricing/rate_card.v2.json).

## Create catalog (rate card v2)

```bash
# Billing Meters (once — meters carry no price, only aggregation)
bash scripts/stripe_create_meters.sh

# v2 Prices: meters at v2 rates, $0 membership, commit tiers, Enterprise —
# all tax_behavior=exclusive
bash scripts/stripe_create_prices_v2.sh
```

Manual CLI sketch:

```bash
stripe billing meters create --display-name "withOhm web fetch" --event-name ohm_web_fetch --default-aggregation[formula]=sum
# … cache_hit / cache_miss similarly
# Metered Prices: unit_amount_decimal matching AT_PRICE_* ; usage_type=metered
```

Set in `.env`:

```
AT_ENV=production
AT_FREE_TIER_FETCH_CAP_DAY=100
AT_DELINQUENT_SUSPEND_DAYS=14
AT_REQUIRE_METER_PRICES=true
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PAYG=price_...          # $0 membership (v2)
STRIPE_PRICE_ENTERPRISE=price_...
STRIPE_PRICE_METER_WEB_FETCH=price_...
STRIPE_PRICE_METER_CACHE_HIT=price_...
STRIPE_PRICE_METER_CACHE_MISS=price_...
STRIPE_PRICE_COMMIT_C29=price_...    # commit tiers (included usage per cycle)
STRIPE_PRICE_COMMIT_C99=price_...
STRIPE_PRICE_COMMIT_C499=price_...
# STRIPE_AUTOMATIC_TAX=true          # after Stripe Tax + origin address in dashboard
STRIPE_METER_EVENT_WEB_FETCH=ohm_web_fetch
STRIPE_METER_EVENT_CACHE_HIT=ohm_cache_hit
STRIPE_METER_EVENT_CACHE_MISS=ohm_cache_miss
```

Forward webhooks (include dunning events — see [STRIPE_DUNNING.md](STRIPE_DUNNING.md)):

```bash
stripe listen --forward-to localhost:8080/v1/billing/webhook \
  --events checkout.session.completed,invoice.paid,invoice.payment_failed,invoice.marked_uncollectible,customer.subscription.updated,customer.subscription.deleted
```

## Self-serve checkout

1. Site `/billing/intermediate` → `POST /v1/billing/checkout` with `plan=payg`, email, organisation, acks
2. Response: `api_key` (once) + `url` (Stripe Checkout)
3. Browser stores key, redirects to Checkout (card on file)
4. Webhook → tenant `active` + `stripe_customer_id`; `invoice.paid` → `billing_paid=true` (lifts fetch soft-cap)
5. Chat / fetch → Redis meters + Stripe `MeterEvent` (quantity aligned to table above)
6. Payment fail → delinquent (fetch locked) → after 14d / cancel → `suspended` → chat **403**

## Admin checkout (ops)

`POST /v1/admin/tenants/{id}/checkout` `{ "plan": "payg" }` — escape hatch when the tenant already exists.

## Lifecycle check (GO_LIVE)

1. Self-serve Intermediate → pay with test card
2. Confirm webhook → tenant `active` + customer id
3. Chat miss + hit + `fetch_web_context` → Redis + Stripe meter events; `GET /v1/usage` shows `stripe_synced`
4. Stripe Dashboard → customer → upcoming invoice preview shows usage
5. Cancel subscription → chat **403**

Success/cancel URLs default to `https://withohm.dev/billing/success|cancel`.

## Design partners

Issue with `"plan": "design_partner"` (no Stripe). Defaults: 90-day expiry, soft USD quota — see `AT_DESIGN_PARTNER_*`.
