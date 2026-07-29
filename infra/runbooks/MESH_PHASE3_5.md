# Phases 3–5 in production (Redis mesh + Anycast)

Run after **`v0.1.0-railgun`** and public miss/hit on `https://api.withohm.dev`.

## Phase 3 — Global Datastore + edge Redis

**Prerequisite:** Leader node type must support Global Datastore (e.g. `cache.r6g.large`, not `cache.t4g.small`).

```powershell
cd infra/terraform
# terraform.tfvars: enable_edges = true, redis_node_type = "cache.r6g.large"
terraform apply
```

Creates:

- `aws_elasticache_global_replication_group.ohm`
- Edge VPCs + peering to leader (`us-west-2`, `eu-west-2` by default)
- Per-edge Global Datastore secondary + RL Redis + EKS

Outputs:

```powershell
terraform output -json edge_wiring
terraform output -json edge_eks_kubeconfig
terraform output -json edge_acm_validation   # add DNS if regional ACM pending
```

Deploy each edge (same manifests as leader; secrets from `edge_wiring`):

```powershell
aws eks update-kubeconfig --region us-west-2 --name at-utility-uswest2-eks
$env:ACM_CERTIFICATE_ARN = "<from edge_wiring us-west-2 acm_certificate_arn>"
bash infra/scripts/k8s_deploy.sh
kubectl -n at-utility get svc gateway-rs -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; Write-Host
# Record NLB ARN for Phase 5
```

Repeat for `eu-west-2`.

**Lag drill** (lab budget &lt;1000ms):

```powershell
.\scripts\redis_global_lag_drill.ps1 -LeaderPrimaryHost master....use1.cache.amazonaws.com -EdgeGetHost <secondary-primary>...
```

## Phase 4 — gateway-rs write path

Leader secret should already use reader/primary split (`leader_redis_env`). Edges use secondary GET + leader SET via `AT_RS_REDIS_WRITE`.

Until Rust RESP speaks TLS, keep `AT_RS_REDIS=127.0.0.1:9` on gateway-rs so auth/cache defers to Python; Python uses `rediss://`.

After TLS RESP: restore real `AT_RS_REDIS` / `AT_RS_REDIS_WRITE` from Terraform outputs.

## Phase 5 — Anycast (Global Accelerator)

Collect NLB ARNs (leader + ≥2 edges):

```powershell
aws elbv2 describe-load-balancers --region us-east-1 --query "LoadBalancers[?Type=='network'].LoadBalancerArn"
```

```hcl
# terraform.tfvars
anycast_enabled      = true
ga_nlb_endpoint_arns = [
  "arn:aws:elasticloadbalancing:us-east-1:...:loadbalancer/net/...",
  "arn:aws:elasticloadbalancing:us-west-2:...:loadbalancer/net/...",
  "arn:aws:elasticloadbalancing:eu-west-2:...:loadbalancer/net/...",
]
```

```powershell
terraform apply
terraform output -json global_accelerator
```

DNS: CNAME `api` → GA DNS name ([API_CUTOVER.md](API_CUTOVER.md) Phase 2). Abort target = recorded leader NLB hostname.

Smoke 60 minutes; run [REGION_DRAIN.md](REGION_DRAIN.md). Then undeffer multi-region claims in [docs/READINESS.md](../../docs/READINESS.md).

## Current status (charged)

- [x] Leader Redis `cache.r6g.large`; Global Datastore `ldgnf-ohm`
- [x] Edges **us-west-2** + **eu-west-2** (EKS, secondaries, NLBs) — [NLB_ARNS.txt](NLB_ARNS.txt)
- [x] Lag drill **PASS** (&lt;1s lab budget)
- [x] GA endpoint groups healthy; DNS `api.withohm.dev` → `a8d1c391c281079a4.awsglobalaccelerator.com`
- [x] Public `external_smoke` **PASS** (SNI + public DNS)
- [ ] Region-drain drill ([REGION_DRAIN.md](REGION_DRAIN.md)) — record below when complete

### Region-drain log

| When (UTC) | Drained | Result | Notes |
|------------|---------|--------|-------|
| _(pending)_ | us-west-2 weight 0 | | Restore after smoke |
