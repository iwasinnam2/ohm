# Incident runbook

## Severity

| Sev | Meaning | Example |
|-----|---------|---------|
| SEV1 | Global outage / wrong bills | All regions 5xx; Stripe charging wrong tenants |
| SEV2 | Single region or provider | One GA endpoint down; OpenAI 429 storm |
| SEV3 | Degraded cache | Hit ratio collapse; lag &gt; budget |

## First five minutes

1. Check status page + GA endpoint health.
2. `GET https://api.<brand>/health` and `GET /v1/providers` with a canary key.
3. Compare OpenAI error rate vs miss ratio (CloudWatch / logs).
4. If OpenAI is down: non-stream traffic may failover to fallback model; stream clients may need reconnect (see [docs/STREAMING.md](../../docs/STREAMING.md)).
5. If Redis leader unavailable: edges can still serve replica GET hits; new misses fail — page Redis on-call.

## Key rotation

1. Issue new tenant keys via `POST /v1/admin/tenants`.
2. Suspend old keys: `POST /v1/admin/tenants/{id}/status` `{"status":"suspended"}`.
3. Rotate `OPENAI_API_KEY` in Secrets Manager; rollout restart gateway pods.
4. Never commit secrets; never paste into chat.

## Budget caps

- OpenAI: hard limit in OpenAI usage dashboard.
- AWS: Budgets alert → SNS.
- Customer: suspend tenant on `invoice.payment_failed` webhook.
