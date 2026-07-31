#!/usr/bin/env bash
# LEGACY (rate card v1) — superseded by scripts/stripe_create_prices_v2.sh,
# which creates the v2 seat/commit/enterprise Prices with tax_behavior set.
# Kept for historical reference only; the $29 credit pack is retired.
# Usage: from repo root after `stripe login`
#   bash scripts/stripe_create_test_prices.sh
set -euo pipefail

if ! command -v stripe >/dev/null 2>&1; then
  echo "Install Stripe CLI: https://stripe.com/docs/stripe-cli" >&2
  exit 1
fi

extract_id() {
  python -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

echo "Creating withOhm Intermediate membership product (\$0 seat)..."
PAYG_PROD=$(stripe products create \
  --name "withOhm Intermediate membership" \
  --description "Card-on-file pipe access; cache + web-fetch metered separately" \
  -d "metadata[billing_model]=seat_plus_meters" | extract_id)
echo "PAYG_PROD=$PAYG_PROD"

echo "Creating Intermediate membership price (\$0 / month)..."
PAYG_PRICE=$(stripe prices create \
  --product "$PAYG_PROD" \
  --unit-amount 0 \
  --currency usd \
  -d "recurring[interval]=month" | extract_id)
echo "STRIPE_PRICE_PAYG=$PAYG_PRICE"

echo "Creating optional \$29 meter credit pack product..."
CREDIT_PROD=$(stripe products create \
  --name "withOhm meter credit pack" \
  --description "Optional \$29 prepaid allowance toward Intermediate meters" \
  -d "metadata[billing_model]=credit_pack" | extract_id)
CREDIT_PRICE=$(stripe prices create \
  --product "$CREDIT_PROD" \
  --unit-amount 2900 \
  --currency usd | extract_id)
echo "STRIPE_PRICE_CREDIT_PACK=$CREDIT_PRICE"

echo "Creating withOhm Enterprise product..."
ENT_PROD=$(stripe products create \
  --name "withOhm Enterprise" \
  --description "Monthly enterprise seat / negotiated bundles" \
  -d "metadata[billing_model]=subscription_seat" | extract_id)
echo "ENT_PROD=$ENT_PROD"

echo "Creating Enterprise monthly price (\$2500)..."
ENT_PRICE=$(stripe prices create \
  --product "$ENT_PROD" \
  --unit-amount 250000 \
  --currency usd \
  -d "recurring[interval]=month" | extract_id)
echo "STRIPE_PRICE_ENTERPRISE=$ENT_PRICE"

cat <<EOF

# Add to .env
STRIPE_PRICE_PAYG=$PAYG_PRICE
STRIPE_PRICE_CREDIT_PACK=$CREDIT_PRICE
STRIPE_PRICE_ENTERPRISE=$ENT_PRICE
# Then run: bash scripts/stripe_create_meters.sh
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
# AT_ENV=production   # fail-closed if meter Prices missing
# Full lifecycle: docs/STRIPE.md
EOF
