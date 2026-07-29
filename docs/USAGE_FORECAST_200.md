# Estimated Intermediate usage — 200 customers

List rates (USD): hit `$0.0005`/1k tok · miss `$0.002`/1k · fetch `$0.001`/URL.  
Membership `$0`. Optional credit pack `$29` ignored in base forecast (upsell).

## Cohort mix (n = 200)

| Segment | Count | Share | Profile |
|---------|------:|------:|---------|
| Indie / solo | 120 | 60% | Light Cursor + occasional browse |
| SMB / small team | 60 | 30% | Daily agents + moderate URL context |
| Larger firm | 20 | 10% | Heavy scrape / multi-seat agents |

## Per-tenant monthly assumptions

| Segment | Tokens/mo | Hit ratio | Fetches/mo | Meter math |
|---------|----------:|----------:|-----------:|------------|
| Indie | 2.0M | 55% | 400 | hit 1.1M → `$0.55`; miss 0.9M → `$1.80`; fetch `$0.40` → **~$2.75** |
| SMB | 12M | 50% | 5,000 | hit 6M → `$3.00`; miss 6M → `$12.00`; fetch `$5.00` → **~$20.00** |
| Larger | 80M | 45% | 40,000 | hit 36M → `$18.00`; miss 44M → `$88.00`; fetch `$40.00` → **~$146.00** |

## Portfolio monthly meter revenue (est.)

| Segment | Tenants × ARPU | Subtotal |
|---------|----------------:|---------:|
| Indie | 120 × $2.75 | **$330** |
| SMB | 60 × $20 | **$1,200** |
| Larger | 20 × $146 | **$2,920** |
| **Total** | **200** | **~$4,450 / mo** |

Annualized meters ≈ **$53k / yr** before Enterprise fixed deals and credit packs.

### Sensitivity

| Scenario | Change | Portfolio / mo |
|----------|--------|----------------:|
| Fetch ×2 on SMB+Large | Browse rocket | ~$6,050 |
| Hit ratio +10pp all | More cache | ~$3,900 |
| 10 Enterprise @ $2.5k seat | Add seats | +$25k (separate SKU) |

If Intermediate were still a flat **$29 seat** with no meters: 200 × $29 = **$5,800 / mo** — similar headline, but **under-prices** the 20 large scrapers (~$146 usage) and **over-prices** 120 indies (~$2.75 usage). Usage-led captures the rocket; $0 membership maximizes attach.

## Ops check

```bash
# After traffic: confirm Redis + Stripe sync
curl -s -H "Authorization: Bearer $OHM_KEY" https://api.withohm.dev/v1/usage | jq .stripe_synced,.revenue_usd,.meter_unit
```

See [STRIPE_DUNNING.md](STRIPE_DUNNING.md) for unpaid invoice enforcement.
