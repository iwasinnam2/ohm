#!/usr/bin/env bash
# Create Stripe *test* Products/Prices for Ohm seat billing (requires stripe CLI).
# Usage: from repo root after `stripe login`
#   bash scripts/stripe_create_test_prices.sh
set -euo pipefail

if ! command -v stripe >/dev/null 2>&1; then
  echo "Install Stripe CLI: https://stripe.com/docs/stripe-cli" >&2
  exit 1
fi

# This CLI build prints JSON by default and rejects --format / -o json.
extract_id() {
  python -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

echo "Creating Ohm PAYG seat product..."
PAYG_PROD=$(stripe products create \
  --name "Ohm PAYG seat" \
  --description "Monthly seat; usage estimated in-product until meters ship" \
  -d "metadata[billing_model]=seat_plus_estimate" | extract_id)
echo "PAYG_PROD=$PAYG_PROD"

echo "Creating PAYG monthly price (\$29)..."
PAYG_PRICE=$(stripe prices create \
  --product "$PAYG_PROD" \
  --unit-amount 2900 \
  --currency usd \
  -d "recurring[interval]=month" | extract_id)
echo "STRIPE_PRICE_PAYG=$PAYG_PRICE"

echo "Creating Ohm Enterprise product..."
ENT_PROD=$(stripe products create \
  --name "Ohm Enterprise" \
  --description "Monthly enterprise seat" \
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
STRIPE_PRICE_ENTERPRISE=$ENT_PRICE
# STRIPE_SECRET_KEY=sk_test_...   # Dashboard → API keys (Test)
# STRIPE_WEBHOOK_SECRET=whsec_... # stripe listen --forward-to localhost:8080/v1/billing/webhook
# Full lifecycle: docs/STRIPE.md
EOF
