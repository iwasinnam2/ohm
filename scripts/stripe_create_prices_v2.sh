#!/usr/bin/env bash
# Rate card v2 (pricing/rate_card.v2.json) — create the full Stripe surface.
# Prices are immutable: this issues NEW v2 Prices alongside v1; existing
# subscriptions keep their old Prices (grandfathered automatically).
#
# Creates:
#   - Metered Prices at v2 rates on the existing Billing Meters
#       cache hit  0.002 / 1k tokens
#       cache miss 0.001 / 1k tokens
#       web fetch  0.003 / URL
#   - $0 Intermediate membership seat
#   - Commit tiers c29 / c99 / c499 (licensed monthly; included usage is
#     granted per cycle by the invoice.paid webhook as a billing credit
#     scoped to metered prices — see src/at_utility/stripe_billing.py)
#   - Enterprise $2,500/mo seat
# All Prices carry tax_behavior=exclusive (Stripe Tax adds on top).
#
# Usage (Stripe CLI logged into the target mode — sandbox now, live at launch):
#   bash scripts/stripe_create_meters.sh        # once, if meters do not exist
#   bash scripts/stripe_create_prices_v2.sh
set -euo pipefail

if ! command -v stripe >/dev/null 2>&1; then
  echo "Install Stripe CLI: https://stripe.com/docs/stripe-cli" >&2
  exit 1
fi

extract_id() {
  python -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

meter_id_for_event() {
  # $1 = meter event_name → resolve the active Billing Meter id
  stripe billing meters list --limit 100 | python -c "
import sys, json
event = '$1'
data = json.load(sys.stdin)
for m in data.get('data', []):
    if m.get('event_name') == event and m.get('status') == 'active':
        print(m['id']); break
else:
    raise SystemExit(f'no active meter for event {event} — run scripts/stripe_create_meters.sh first')
"
}

echo "Resolving Billing Meters..."
HIT_METER=$(meter_id_for_event ohm_cache_hit)
MISS_METER=$(meter_id_for_event ohm_cache_miss)
FETCH_METER=$(meter_id_for_event ohm_web_fetch)
echo "HIT_METER=$HIT_METER MISS_METER=$MISS_METER FETCH_METER=$FETCH_METER"

echo "Creating v2 metered Prices (tax exclusive)..."
HIT_PROD=$(stripe products create \
  --name "withOhm cache hit (v2)" \
  --description "Redis identical-request replay rent (per 1k tokens)" \
  -d "metadata[meter]=ohm_cache_hit" \
  -d "metadata[rate_card]=2" | extract_id)
HIT_PRICE=$(stripe prices create \
  --product "$HIT_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$HIT_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.2" \
  -d "tax_behavior=exclusive" \
  -d "metadata[rate_card]=2" | extract_id)

MISS_PROD=$(stripe products create \
  --name "withOhm cache miss (v2)" \
  --description "Pipe proxy fee on cache miss (per 1k tokens)" \
  -d "metadata[meter]=ohm_cache_miss" \
  -d "metadata[rate_card]=2" | extract_id)
MISS_PRICE=$(stripe prices create \
  --product "$MISS_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$MISS_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.1" \
  -d "tax_behavior=exclusive" \
  -d "metadata[rate_card]=2" | extract_id)

FETCH_PROD=$(stripe products create \
  --name "withOhm web fetch (v2)" \
  --description "Compliant URL ingest (per URL)" \
  -d "metadata[meter]=ohm_web_fetch" \
  -d "metadata[rate_card]=2" | extract_id)
FETCH_PRICE=$(stripe prices create \
  --product "$FETCH_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$FETCH_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.3" \
  -d "tax_behavior=exclusive" \
  -d "metadata[rate_card]=2" | extract_id)

echo "Creating \$0 Intermediate membership (v2, tax exclusive)..."
PAYG_PROD=$(stripe products create \
  --name "withOhm Intermediate membership (v2)" \
  --description "Card-on-file pipe access; cache + web-fetch metered separately" \
  -d "metadata[billing_model]=seat_plus_meters" \
  -d "metadata[rate_card]=2" | extract_id)
PAYG_PRICE=$(stripe prices create \
  --product "$PAYG_PROD" \
  --unit-amount 0 \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "tax_behavior=exclusive" \
  -d "metadata[rate_card]=2" | extract_id)

echo "Creating commit tiers c29 / c99 / c499..."
create_commit() {
  # $1 = tier id, $2 = usd/month cents, $3 = included usd
  local prod price
  prod=$(stripe products create \
    --name "withOhm commit $1" \
    --description "\$$(( $2 / 100 ))/mo commit — \$$3 metered usage included each cycle" \
    -d "metadata[billing_model]=commit_tier" \
    -d "metadata[commit_tier]=$1" \
    -d "metadata[included_usd]=$3" \
    -d "metadata[rate_card]=2" | extract_id)
  price=$(stripe prices create \
    --product "$prod" \
    --unit-amount "$2" \
    --currency usd \
    -d "recurring[interval]=month" \
    -d "tax_behavior=exclusive" \
    -d "metadata[commit_tier]=$1" \
    -d "metadata[included_usd]=$3" \
    -d "metadata[rate_card]=2" | extract_id)
  echo "$price"
}
C29_PRICE=$(create_commit c29 2900 35)
C99_PRICE=$(create_commit c99 9900 125)
C499_PRICE=$(create_commit c499 49900 700)

echo "Creating Enterprise \$2,500/mo (v2, tax exclusive)..."
ENT_PROD=$(stripe products create \
  --name "withOhm Enterprise (v2)" \
  --description "Monthly enterprise seat / negotiated bundles" \
  -d "metadata[billing_model]=subscription_seat" \
  -d "metadata[rate_card]=2" | extract_id)
ENT_PRICE=$(stripe prices create \
  --product "$ENT_PROD" \
  --unit-amount 250000 \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "tax_behavior=exclusive" \
  -d "metadata[rate_card]=2" | extract_id)

cat <<EOF

# Rate card v2 — add to the API environment (k8s secret / .env)
STRIPE_PRICE_PAYG=$PAYG_PRICE
STRIPE_PRICE_ENTERPRISE=$ENT_PRICE
STRIPE_PRICE_METER_CACHE_HIT=$HIT_PRICE
STRIPE_PRICE_METER_CACHE_MISS=$MISS_PRICE
STRIPE_PRICE_METER_WEB_FETCH=$FETCH_PRICE
STRIPE_PRICE_COMMIT_C29=$C29_PRICE
STRIPE_PRICE_COMMIT_C99=$C99_PRICE
STRIPE_PRICE_COMMIT_C499=$C499_PRICE
# Optional after dashboard Stripe Tax activation + origin address:
# STRIPE_AUTOMATIC_TAX=true

# Meter quantity: ceil(tokens/1000) for hit/miss; URL count for fetch.
# Governance: docs/PRICING.md — never edit prices, issue v3.
EOF
