# Observability

## Metrics to centralize

| Metric | Why |
|--------|-----|
| Request rate by region | Traffic shift / drain |
| Cache miss ratio | Arbitrage health (collapse = good product; spike = cold cache or bug) |
| OpenAI / Anthropic error rate | Upstream pain |
| Replica lag (bytes / seconds) | Section D budget |
| Regional latency p50/p99 | Anycast effectiveness |
| Stripe webhook failures | Customer ledger drift |

## Alerts (suggested)

- OpenAI error rate &gt; 5% for 5 minutes → SEV2
- Miss ratio &gt; 95% for 30 minutes with traffic → investigate cache/Redis
- Any GA endpoint unhealthy &gt; 2 minutes → page
- Replica lag &gt; 5s → SEV3

## Logs

- Gateway: structured JSON with `tenant_id`, `cache=HIT|MISS`, `provider`, `region`
- Rust edge: `x-at-plane: rust` proven in smoke
- Never log full prompts in production by default (PII / training-data risk); hash cache keys only
