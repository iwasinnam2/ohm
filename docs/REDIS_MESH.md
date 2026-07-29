# Redis mesh — phases and wiring

Source of truth for leader/replica/global distribution. Consistency rules: [CONSISTENCY.md](CONSISTENCY.md). Topology playbook: [infra/README.md](../infra/README.md).

## Verdict

| Phase | Goal | In-repo | Live traffic |
|-------|------|---------|--------------|
| 0 | Single-region public deck Redis | Templates ready | Blocked on [GO_LIVE.md](../infra/runbooks/GO_LIVE.md) API cutover |
| 1 | Local primary+replica split + lag smoke | Compose + `scripts/redis_replica_smoke.ps1` | Local only |
| 2 | Leader `REDIS_URL`=reader, `REDIS_WRITE_URL`=primary | Secrets + outputs | After Section C apply |
| 3 | Global Datastore secondaries + edge env | Terraform when `enable_edges=true` | After Phase 0 |
| 4 | `AT_RS_REDIS_WRITE` on gateway-rs | Implemented | Deploy image |
| 5 | Anycast | GA Terraform gated on NLB ARNs | After ≥2 edges + lag drill |

Do **not** claim Redis lag budgets or Anycast in marketing until Phase 3–5 are green in production.

## Env pattern

| Variable | Role |
|----------|------|
| `REDIS_URL` | Local/reader GET (prompt cache hits) |
| `REDIS_WRITE_URL` | Leader primary SET, metering, tenants |
| `REDIS_RL_URL` | Regional writable token buckets |
| `AT_RS_REDIS` | Rust GET endpoint (host:port, no `redis://`) |
| `AT_RS_REDIS_WRITE` | Rust SET endpoint; defaults to `AT_RS_REDIS` if unset |

## Cache key (Python = Rust)

Digest = SHA-256 of canonical JSON:

```json
{"extras":{...},"messages":[...],"model":"..."}
```

`sort_keys=true`, separators `,` `:`. Extras keys match Python chat path (`fetch_web_context`, `web_*`, `temperature`, `max_tokens`, `cache_control`).

Tenant prefix:

- Bootstrap keys in `AT_API_KEYS` → `tenant_bootstrap_{last8}`
- Issued keys → Redis lookup `at:global:apikey:{sha256(key)}` (GET on read client)

## Phase 0 — single-region public

1. Terraform Section C: leader ElastiCache multi-AZ.
2. K8s secret (all three URLs may point at **primary** until Phase 2):

```bash
REDIS_URL=rediss://PRIMARY:6379/0
REDIS_WRITE_URL=rediss://PRIMARY:6379/0
REDIS_RL_URL=rediss://PRIMARY:6379/0
AT_RS_REDIS=PRIMARY:6379
AT_RS_REDIS_WRITE=PRIMARY:6379
```

3. Confirm `X-AT-Cache: HIT|MISS` and `/v1/usage` on `https://api.withohm.dev` after cutover.

## Phase 1 — local smoke

```powershell
docker compose up -d redis redis-replica
.\scripts\redis_replica_smoke.ps1
```

Lab lag budget: **&lt;1000ms** from primary SET to replica GET.

## Phase 2 — same-region reader

Set `REDIS_URL` / `AT_RS_REDIS` to ElastiCache **reader_endpoint**; keep writes on **primary**. Secrets Manager bootstrap encodes this when Terraform applies.

## Phase 3 — Global Datastore

`enable_edges=true` → `aws_elasticache_global_replication_group` + per-edge secondary RGs. Edge outputs fill real `REDIS_URL`. Allotment CronJob already uses `REDIS_WRITE_URL` as leader.

## Phase 4–5

Rust never SETs on a replica when `AT_RS_REDIS_WRITE` is set. Anycast: `anycast_enabled=true` + `ga_nlb_endpoint_arns` after lag drill; then undeffer claims in [READINESS.md](READINESS.md).
