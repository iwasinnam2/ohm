# Estimated Intermediate usage — 200 customers

List rates (USD, rate card v2): hit `$0.002`/1k tok · miss `$0.001`/1k · fetch `$0.003`/URL.  
Membership `$0`. Commit tiers (c29/c99/c499) ignored in base forecast — they set a fixed floor, not a change in metered totals. Recompute any time: `python scripts/estimate_usage_200.py` (reads the canonical rate card).

## Cohort mix (n = 200)

| Segment | Count | Share | Profile |
|---------|------:|------:|---------|
| Indie / solo | 120 | 60% | Light Cursor + occasional browse |
| SMB / small team | 60 | 30% | Daily agents + moderate URL context |
| Larger firm | 20 | 10% | Heavy scrape / multi-seat agents |

## Per-tenant monthly assumptions

| Segment | Tokens/mo | Hit ratio | Fetches/mo | Meter math |
|---------|----------:|----------:|-----------:|------------|
| Indie | 2.0M | 55% | 400 | hit 1.1M → `$2.20`; miss 0.9M → `$0.90`; fetch `$1.20` → **~$4.30** |
| SMB | 12M | 50% | 5,000 | hit 6M → `$12.00`; miss 6M → `$6.00`; fetch `$15.00` → **~$33.00** |
| Larger | 80M | 45% | 40,000 | hit 36M → `$72.00`; miss 44M → `$44.00`; fetch `$120.00` → **~$236.00** |

## Portfolio monthly meter revenue (est.)

| Segment | Tenants × ARPU | Subtotal |
|---------|----------------:|---------:|
| Indie | 120 × $4.30 | **$516** |
| SMB | 60 × $33 | **$1,980** |
| Larger | 20 × $236 | **$4,720** |
| **Total** | **200** | **~$7,216 / mo** |

Annualized meters ≈ **$87k / yr** before Enterprise fixed deals and commit-tier floors. (Rate card v1 forecast the same cohort at ~$4,450/mo — v2 lifts value capture ~62% while *cutting* the per-call miss tax in half.)

### Sensitivity

| Scenario | Change | Portfolio / mo |
|----------|--------|----------------:|
| Fetch ×2 on SMB+Large | Browse rocket | ~$10,500 |
| Hit ratio +10pp all | More cache | ~$7,470 (hits now out-earn misses — cache growth raises revenue) |
| 10 Enterprise @ $2.5k seat | Add seats | +$25k (separate SKU) |
| 30 SMB adopt c99 commit | Fixed floor | $2,970/mo floor regardless of usage dips |

If Intermediate were a flat **$29 seat** with no meters: 200 × $29 = **$5,800 / mo** — similar headline, but it under-prices the 20 large scrapers (~$236 usage) and over-prices 120 indies (~$4.30 usage). Usage-led captures the rocket; $0 membership maximizes attach; commit tiers give finance a fixed line without breaking the meter logic.

## Ops check

```bash
# After traffic: confirm Redis + Stripe sync
curl -s -H "Authorization: Bearer $OHM_KEY" https://api.withohm.dev/v1/usage | jq .stripe_synced,.revenue_usd,.meter_unit
```

See [STRIPE_DUNNING.md](STRIPE_DUNNING.md) for unpaid invoice enforcement.
