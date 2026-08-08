# Multi-region Redis mesh + Anycast edge

> **Current posture (Jul 2026): single-region us-east-1.** The mesh below was
> live and has been torn down until paid traffic justifies it (burn control).
> See [runbooks/SINGLE_REGION.md](runbooks/SINGLE_REGION.md) for what runs
> today and how to re-enable the mesh.

## Topology

- **Leader** (`us-east-1` by default): all cache `SET`s, metering ledger writes, global quota grants (ElastiCache replication group).
- **Replicas** (`us-west-2`, `eu-west-2`, `ap-northeast-1`): colocated with gateway pods; local `GET` for cache hits.
- **Regional RL Redis**: writable ElastiCache node per edge for token-bucket allotments (replicas are read-only).
- **Anycast** (Section E): AWS Global Accelerator advertises one IP; health-checks Rust `/health`.

## Consistency boundary

Cache replication is **asynchronous**. A hit in London may lag a Virginia write by tens to hundreds of milliseconds (budget: **&lt;1s** in testing). That is acceptable for prompt-response cache. **Billing and tenant status are not served from replicas** — they use leader writes (`REDIS_WRITE_URL`) and the durable daily ledger from Section B.

## Gateway env (edge)

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Local replica / reader — `GET` |
| `REDIS_WRITE_URL` | Leader primary — `SET`, metering, tenants |
| `REDIS_RL_URL` | Local RL cluster — token buckets |
| `AT_RS_REDIS` | Rust GET (replica/reader host:port) |
| `AT_RS_REDIS_WRITE` | Rust SET (leader primary host:port) |
| `AT_REGION` | Region name for keys `at:{tenant}:rl:{region}` |

## Section C — first region

1. Create AWS account; enable **Billing alarms**.
2. Bootstrap state: `bash infra/scripts/bootstrap_state.sh`
3. Copy `infra/terraform/backend.hcl.example` → `backend.hcl`, `terraform init -backend-config=backend.hcl`
4. `terraform apply` (leader VPC + Redis + ECR + Secrets + ACM)
5. Push images: `bash infra/scripts/ecr_push.sh 0.1.0`
6. Create K8s secret from `terraform output -json leader_redis_env` (Phase 2 reader/primary split):

```bash
# Phase 0 cutover may temporarily point REDIS_URL at PRIMARY; prefer reader once stable.
PRIMARY=$(terraform output -raw redis_leader_primary_endpoint)
READER=$(terraform output -raw redis_leader_reader_endpoint)
kubectl -n at-utility create secret generic at-utility-secrets \
  --from-literal=AT_API_KEYS=sk-at-... \
  --from-literal=AT_ADMIN_API_KEYS=sk-at-... \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=REDIS_URL=rediss://${READER}:6379/0 \
  --from-literal=REDIS_WRITE_URL=rediss://${PRIMARY}:6379/0 \
  --from-literal=REDIS_RL_URL=rediss://${PRIMARY}:6379/0 \
  --from-literal=AT_RS_REDIS=${READER}:6379 \
  --from-literal=AT_RS_REDIS_WRITE=${PRIMARY}:6379
```

7. Deploy: `ACM_CERTIFICATE_ARN=$(terraform output -raw acm_certificate_arn) bash infra/scripts/k8s_deploy.sh`
8. Capture NLB hostname; smoke; [API_CUTOVER.md](runbooks/API_CUTOVER.md) Phase 1.

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-...
```

See also [docs/REDIS_MESH.md](../docs/REDIS_MESH.md).

## Section D — edge mesh

1. Set `enable_edges = true` in `terraform.tfvars` and `terraform apply`.
2. Terraform creates `aws_elasticache_global_replication_group` + per-edge secondary RGs and RL clusters; `edge_wiring` outputs real `REDIS_URL` / `AT_RS_REDIS`.
3. Deploy the same manifests per region with edge env from module outputs (`edge_wiring`).
4. CronJob runs `python -m at_utility.allotment` every minute.

### Lag budget drill

After a miss/`SET` in the leader region, measure time until `GET` hits in two edge regions. Record p50/p99; target under **1000ms** in lab conditions.

Local (Phase 1):

```powershell
.\scripts\redis_replica_smoke.ps1
```

## Section E — Anycast

Prerequisites: ≥2 healthy regional NLBs, Phase 3 lag drill green, public API miss/hit proven.

1. Set `anycast_enabled = true` and `ga_nlb_endpoint_arns = ["arn:aws:elasticloadbalancing:..."]`.
2. `terraform apply` — accelerator, listener, endpoint group.
3. Cut DNS `api.withohm.dev` → GA DNS name — [API_CUTOVER.md](runbooks/API_CUTOVER.md) Phase 2.
4. Drain one region endpoint; confirm clients continue without config change.
5. Checklist: [GO_LIVE.md](runbooks/GO_LIVE.md).
6. After green: undeffer multi-region/Anycast claims in [docs/READINESS.md](../docs/READINESS.md).

## Status host

`status.withohm.dev` may remain on Amplify for DNS continuity. Middleware **308-redirects** to `https://www.withohm.dev/docs/status`. The public `/status` UI is retired (404).

## Rate limits

Gateways decrement **regional token buckets** (`at:{tenant}:rl:{region}`) on `REDIS_RL_URL` using a fixed rate/burst from `Settings` (`at_rate_limit_rps` / `at_rate_limit_burst`) — not yet the allotment cron's output. The allotment refresher (`python -m at_utility.allotment`) already copies `at:global:quota:{region}` to `at:global:allotment:{region}` on the edge Redis every minute; wiring the token-bucket call to read that key as a per-region rate/burst override is still open (see `src/at_utility/allotment.py` module docstring).
