#!/usr/bin/env bash
# Create Stripe Billing Meters + metered Prices aligned to AT_PRICE_* units.
# Quantity model (see src/at_utility/metering.py):
#   ohm_cache_hit / ohm_cache_miss → ceil(tokens/1000) billable units
#   ohm_web_fetch → URL count
# Unit amounts (USD): hit 0.0005, miss 0.002, fetch 0.001
#
# Usage (requires Stripe CLI logged into test or live mode):
#   bash scripts/stripe_create_meters.sh
set -euo pipefail

if ! command -v stripe >/dev/null 2>&1; then
  echo "Install Stripe CLI: https://stripe.com/docs/stripe-cli" >&2
  exit 1
fi

extract_id() {
  python -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

echo "Creating Billing Meters..."
HIT_METER=$(stripe billing meters create \
  --display-name "withOhm cache hit (per 1k tokens)" \
  --event-name ohm_cache_hit \
  -d "default_aggregation[formula]=sum" | extract_id)
echo "HIT_METER=$HIT_METER"

MISS_METER=$(stripe billing meters create \
  --display-name "withOhm cache miss (per 1k tokens)" \
  --event-name ohm_cache_miss \
  -d "default_aggregation[formula]=sum" | extract_id)
echo "MISS_METER=$MISS_METER"

FETCH_METER=$(stripe billing meters create \
  --display-name "withOhm web fetch (per URL)" \
  --event-name ohm_web_fetch \
  -d "default_aggregation[formula]=sum" | extract_id)
echo "FETCH_METER=$FETCH_METER"

echo "Creating meter Products..."
HIT_PROD=$(stripe products create \
  --name "withOhm cache hit" \
  --description "Redis identical-request replay rent (per 1k tokens)" \
  -d "metadata[meter]=ohm_cache_hit" | extract_id)
MISS_PROD=$(stripe products create \
  --name "withOhm cache miss" \
  --description "Pipe proxy fee on cache miss (per 1k tokens)" \
  -d "metadata[meter]=ohm_cache_miss" | extract_id)
FETCH_PROD=$(stripe products create \
  --name "withOhm web fetch" \
  --description "Compliant URL ingest (per URL)" \
  -d "metadata[meter]=ohm_web_fetch" | extract_id)

echo "Creating metered Prices (per_unit, monthly)..."
HIT_PRICE=$(stripe prices create \
  --product "$HIT_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$HIT_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.0005" | extract_id)

MISS_PRICE=$(stripe prices create \
  --product "$MISS_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$MISS_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.002" | extract_id)

FETCH_PRICE=$(stripe prices create \
  --product "$FETCH_PROD" \
  --currency usd \
  -d "recurring[interval]=month" \
  -d "recurring[usage_type]=metered" \
  -d "recurring[meter]=$FETCH_METER" \
  -d "billing_scheme=per_unit" \
  -d "unit_amount_decimal=0.001" | extract_id)

cat <<EOF

# Add to .env (metered Intermediate — required when AT_ENV=production)
STRIPE_PRICE_METER_CACHE_HIT=$HIT_PRICE
STRIPE_PRICE_METER_CACHE_MISS=$MISS_PRICE
STRIPE_PRICE_METER_WEB_FETCH=$FETCH_PRICE
STRIPE_METER_EVENT_CACHE_HIT=ohm_cache_hit
STRIPE_METER_EVENT_CACHE_MISS=ohm_cache_miss
STRIPE_METER_EVENT_WEB_FETCH=ohm_web_fetch

# Also create a \$0 Intermediate membership seat:
#   bash scripts/stripe_create_test_prices.sh
# Prefer STRIPE_PRICE_PAYG from the \$0 membership price, not \$29.

# Meter quantity: ceil(tokens/1000) for hit/miss; URL count for fetch.
# Docs: docs/STRIPE.md
EOF
