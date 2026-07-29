# Stripe (withOhm)

## Billing model

| Layer | Behavior |
|-------|----------|
| **Membership seat** | Monthly subscription via Checkout (`mode=subscription`, qty 1). Intermediate default is **$0** (card on file). |
| **Meters** | Stripe Billing Meters: `ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss` — events synced from Redis metering |
| **Credit pack (optional)** | `$29` prepaid allowance (`STRIPE_PRICE_CREDIT_PACK`) — not the growth hero price |
| **Dunning (1–14d)** | First `invoice.payment_failed` → delinquent (fetch **402**); Stripe Smart Retries + emails; day ≥`AT_DELINQUENT_SUSPEND_DAYS` → **403**. See [STRIPE_DUNNING.md](STRIPE_DUNNING.md) |
| **Suspend** | `customer.subscription.deleted` / `invoice.marked_uncollectible` / sub `canceled`\|`unpaid` → tenant `suspended` → **403** |
| **Fetch soft-cap** | `AT_FREE_TIER_FETCH_CAP_DAY` (default 100) until `invoice.paid` / metered spend unlocks Intermediate |

Checkout line items: seat Price + **all three** metered Prices (required when `AT_ENV=production` or `AT_REQUIRE_METER_PRICES=true`).

### Meter units (must match Prices)

| Event | Stripe quantity | List USD (`AT_PRICE_*`) |
|-------|-----------------|-------------------------|
| `ohm_cache_hit` | `ceil(tokens/1000)` (min 1) | `$0.0005` / 1k tokens |
| `ohm_cache_miss` | `ceil(tokens/1000)` (min 1) | `$0.002` / 1k tokens |
| `ohm_web_fetch` | URL count | `$0.001` / URL |

## Create test catalog

```bash
# Seat ($0 Intermediate) + optional $29 credit pack + Enterprise seat
bash scripts/stripe_create_test_prices.sh

# Billing Meters + metered Prices (required for Intermediate in production)
bash scripts/stripe_create_meters.sh
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
STRIPE_PRICE_PAYG=price_...          # prefer $0 membership
STRIPE_PRICE_CREDIT_PACK=price_...   # optional $29
STRIPE_PRICE_ENTERPRISE=price_...
STRIPE_PRICE_METER_WEB_FETCH=price_...
STRIPE_PRICE_METER_CACHE_HIT=price_...
STRIPE_PRICE_METER_CACHE_MISS=price_...
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
