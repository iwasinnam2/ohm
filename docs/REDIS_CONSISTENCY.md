# Redis consistency expectations

| Data | Consistency | Store |
|------|-------------|--------|
| Prompt cache | Eventually consistent (async replica) | Local GET / leader SET |
| Rate-limit buckets | Regional, eventual allotments | `REDIS_RL_URL` |
| Usage ledger / billing | Strong enough for invoices (leader writes) | `REDIS_WRITE_URL` |
| Tenant status | Leader | `REDIS_WRITE_URL` |

**Do not** use Redis prompt-cache replicas for bank balances or entitlement checks that must be strongly consistent. Suspended tenants and Stripe state always resolve from the leader-backed tenant registry.

Gateway-rs: `AT_RS_REDIS` (GET) / `AT_RS_REDIS_WRITE` (SET). Cache digests match Python (`docs/REDIS_MESH.md`). Phased rollout: local smoke → same-region reader → Global Datastore → Anycast.