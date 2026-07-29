# Stripe (Ohm)

## Billing model

| Layer | Behavior |
|-------|----------|
| **Seat** | Monthly subscription via Checkout (`mode=subscription`, qty 1) |
| **Meters** | Stripe Billing Meters: `ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss` — events synced from Redis metering |
| **Suspend** | `customer.subscription.deleted` / `invoice.payment_failed` → tenant `suspended` → **403** |

Checkout line items: seat Price + metered Prices (when configured). Meter events use `stripe_customer_id` on the tenant.

## Test Products / Prices / Meters

```bash
# Requires Stripe CLI + test secret key
stripe products create --name "Ohm PAYG seat" --description "Monthly pipe access; usage metered separately"
stripe prices create --product prod_XXX --unit-amount 2900 --currency usd --recurring[interval]=month

stripe products create --name "Ohm Enterprise"
stripe prices create --product prod_YYY --unit-amount 250000 --currency usd --recurring[interval]=month

# Meters (event names must match env)
stripe billing meters create --display-name "Ohm web fetch" --event-name ohm_web_fetch --default-aggregation[formula]=sum
stripe billing meters create --display-name "Ohm cache hit" --event-name ohm_cache_hit --default-aggregation[formula]=sum
stripe billing meters create --display-name "Ohm cache miss" --event-name ohm_cache_miss --default-aggregation[formula]=sum

# Metered prices (attach to meter IDs from dashboard/CLI; unit amounts match AT_PRICE_* in cents if desired)
# Example: $0.001 per fetch → unit_amount_decimal / billing scheme per Stripe meter price docs
```

Set in `.env`:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PAYG=price_...
STRIPE_PRICE_ENTERPRISE=price_...
STRIPE_PRICE_METER_WEB_FETCH=price_...
STRIPE_PRICE_METER_CACHE_HIT=price_...
STRIPE_PRICE_METER_CACHE_MISS=price_...
STRIPE_METER_EVENT_WEB_FETCH=ohm_web_fetch
STRIPE_METER_EVENT_CACHE_HIT=ohm_cache_hit
STRIPE_METER_EVENT_CACHE_MISS=ohm_cache_miss
```

Forward webhooks:

```bash
stripe listen --forward-to localhost:8080/v1/billing/webhook
```

## Self-serve checkout

1. Site `/billing` → `POST /v1/billing/checkout` with `plan`, `label`, `terms_ack`, `dpa_ack`
2. Response: `api_key` (once) + `url` (Stripe Checkout)
3. Browser stores key, redirects to Checkout
4. Webhook → tenant `active` + `stripe_customer_id`
5. Cancel / fail → `suspended` → chat **403**

## Admin checkout (ops)

`POST /v1/admin/tenants/{id}/checkout` `{ "plan": "payg" }` — escape hatch when the tenant already exists.

## Lifecycle check (GO_LIVE)

1. Self-serve or admin issue + checkout → pay with test card
2. Confirm webhook → tenant `active` + customer id
3. Chat / fetch → Redis meters + Stripe meter events (when customer id present)
4. Cancel subscription → chat **403**

Success/cancel URLs default to `https://withohm.dev/billing/success|cancel`.

## Design partners

Issue with `"plan": "design_partner"` (no Stripe). Defaults: 90-day expiry, soft USD quota — see `AT_DESIGN_PARTNER_*`.
