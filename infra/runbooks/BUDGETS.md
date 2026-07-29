# Budgets & spend alarms (withOhm)

## AWS (done)

| Item | Value |
|------|--------|
| Budget | `withohm-monthly` — **$250 / month** cost |
| Alerts | 80% and 100% of budget (ACTUAL) |
| SNS | `arn:aws:sns:us-east-1:594161136574:withohm-budget-alerts` |
| Email | `admin@withohm.dev` — **confirm the SNS subscription** in inbox |

Legacy joke budget `Test Fuckery` ($100) can be deleted in Budgets console when you want.

```powershell
aws budgets describe-budget --account-id 594161136574 --budget-name withohm-monthly --region us-east-1
```

## OpenAI (you — platform ledger)

1. https://platform.openai.com/settings/organization/limits  
2. Set a hard monthly budget (suggest **$100–200** for early traffic; raise later).  
3. Enable email alerts at 50% / 80% / 100%.  
4. Keep Intermediate **BYOK** so customer keys absorb most model spend; Ohm’s org key is only for managed/enterprise pools.

## Stripe Radar / billing

Sandbox account `Ohm sandbox` — enable Dashboard Smart Retries (8 / 2 weeks) + failed-payment emails per [STRIPE_DUNNING.md](../../docs/STRIPE_DUNNING.md).
