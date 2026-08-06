# AWS cost slim (pre-revenue) — keep the architecture

No teardown. EKS, Redis, NAT, NLB, VPC stay. We only **right-size** and
drop unused HA / metering fat. Mesh used to be **$1.5–2k/mo**; that is
already gone. A ~**$100** bill with the API up is mostly the always-on floor.

## Where the money goes (us-east-1, API live)

| Line | Approx/mo | Slimmed how? |
|------|-----------|--------------|
| EKS control plane | ~$73 | Keep (architecture) |
| 1× `t3.medium` node | ~$30 | Keep desired=1; do **not** drop to 2 GiB (`t3.small`) — OOM risk |
| Redis | ~$23–46 | **1× `t4g.small`** (~half of Multi-AZ); see below |
| NAT Gateway + EIP + data | ~$33+ | Keep (1 NAT already) |
| NLB | ~$16–25 | Keep |
| Route53 health checks | ~$1–3 | Latency metering **off** |
| Amplify | low tens | Master-only; kill feature-branch apps in console |
| Global Accelerator / edges | $0 | Keep `anycast_enabled=false`, `enable_edges=false` |

Neon Postgres is a **separate** Neon invoice — see [NEON.md](NEON.md).

## Terraform slim defaults (this PR)

| Knob | Pre-revenue value | Resume later |
|------|-------------------|--------------|
| `redis_num_cache_clusters` | `1` (no Multi-AZ / failover) | `2` |
| `redis_node_type` | `cache.t4g.small` | `cache.r6g.large` only for mesh |
| `redis_snapshot_retention_days` | `3` | `7` |
| `eks_desired_nodes` | `1` | scale up with traffic |
| Route53 `measure_latency` | `false` | optional |
| ECR lifecycle | keep last **15** images | raise if needed |

Apply after merge (`infra/terraform`):

```powershell
cd infra/terraform
terraform plan
# Expect: Redis replica removal / Multi-AZ off, snapshot retention 3,
# health-check replace (latency off), ECR lifecycle create.
terraform apply
```

Redis 2→1 is a **modify**, not a destroy of the replication group. Accept the
tradeoff: one AZ/node loss means restore from ElastiCache snapshot until you
set `redis_num_cache_clusters = 2` again.

## Operator console (no TF)

1. **Cost Explorer → Group by Service** — confirm no leftover
   `AWSGlobalAccelerator` / edge-region EKS/NAT.
2. **Amplify** — delete feature-branch apps; keep `master` / production only
   (`AMPLIFY_SITE.md` still lists old preview URLs).
3. **SNS email** — unsubscribe mailbox delivery ([EMAIL_ALERTS.md](EMAIL_ALERTS.md) if merged).
4. **Neon** — turn on scale-to-zero (suspend 300s); history is already Free **6h**
   — leave it (do not set to 0; History $0 on Free). Cost win is scale-to-zero,
   not the history slider. No snapshot schedules yet ([NEON.md](NEON.md)).

## Do not do (architecture destroy / high risk)

- `enable_eks = false`, destroy Redis / NAT / NLB / VPC
- EKS `t3.small` / `t4g.small` (2 GiB) — pod requests already crowded
- EKS `t4g.medium` until images are multi-arch (CI builds amd64 only today)
- `redis_node_type = cache.t4g.micro` without a memory headroom check
- Re-enable `enable_edges` / `anycast_enabled` / `cache.r6g.large` pre-revenue

## Footguns that recreate a fat bill

- Applying with `redis_node_type = cache.r6g.large`
- `eks_desired_nodes = 2` or `redis_num_cache_clusters = 2` without need
- `enable_edges = true`

## Resume after revenue

1. `redis_num_cache_clusters = 2` → Multi-AZ + failover back on.
2. `redis_snapshot_retention_days = 7`.
3. Mesh / GA / `r6g.large` only with paid traffic — [MESH_PHASE3_5.md](MESH_PHASE3_5.md).
