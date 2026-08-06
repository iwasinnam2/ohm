# Single-region posture (Jul 2026)

withOhm serves all traffic from **us-east-1**: EKS (`at-utility-eks`, 1×
t3.medium) running `gateway` (Python control plane), `gateway-rs` (Rust edge),
and `ingest-worker`, in front of ElastiCache Redis (`at-utility-redis-leader`,
TLS, daily snapshots). Pre-revenue Terraform defaults slim Redis to **1×
`cache.t4g.small`** (no Multi-AZ) and **3-day** snapshot retention — same
architecture, less HA fat; set `redis_num_cache_clusters = 2` when HA matters
again. The mesh (us-west-2 + eu-west-2 edges, Global Datastore, Global
Accelerator) was torn down to cut burn from ~$1.5–2k/mo toward <$200/mo.
Terraform keeps the mesh behind `enable_edges` / `anycast_enabled` for when
paid traffic justifies it.

## Region notes

- `AT_REGION` stays `us-east-1` on the leader. Setting it to an edge region
  name on a pod that writes through to Redis will mis-route cache-key metadata
  — only set it when a real edge deployment returns (this note used to live in
  `infra/k8s/manifests.yaml`).
- Redis GET/SET both land on the leader replication group (reader + primary
  endpoints). No Global Datastore.

## Teardown state

Done (Jul 30):

- eu-west-2 + us-west-2: k8s namespaces deleted (NLBs released), full edge
  stacks destroyed via targeted `terraform apply`.
- Global Datastore `ldgnf-ohm` destroyed (us-west-2 secondary disassociated
  via the us-east-1 API during the regional outage).
- Leader right-sized: node group desired=1 (t3.medium), Redis
  `cache.t4g.small`, snapshots 7d (window 05:00-07:00), stale edge routes
  removed.
- Leader manifests: liveness probes, `/ready` readiness on gateway, edge-hit
  secret wiring, images `0.1.9`.
- Redis SG ingress moved out of inline rules (inline rules are exclusive; a
  reconciliation once stripped the VPC rule and cut pods off from Redis).

Remaining — ONLY the Global Accelerator, kept alive so `api.withohm.dev`
(CNAME -> GA) stays up. After the GoDaddy DNS flip below, finish with:

```powershell
cd infra/terraform
terraform plan    # should show only the 5 globalaccelerator resources
terraform apply   # destroys GA; saves ~$20-40/mo
```

## DNS (GoDaddy — operator step, do BEFORE the GA teardown apply)

`api.withohm.dev` is currently a CNAME to the Global Accelerator
(`a8d1c391c281079a4.awsglobalaccelerator.com`). Point it at the us-east-1 NLB
so the GA teardown causes no outage:

```text
CNAME  api  a8a4fb2a5e7214a93bc86c9b79a4f3c6-da5bb54336e41479.elb.us-east-1.amazonaws.com  (TTL 600)
```

Verify: `curl https://api.withohm.dev/health` → `{"ok":true,...,"plane":"rust"}`.

## Edge HIT metering secret (operator step)

Metered cache HITs at the Rust edge require a shared secret in the cluster
secret. Until it is set the edge full-proxies (Python meters every request —
fail-safe, slightly slower HITs):

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((-join ($bytes | % { $_.ToString('x2') }))))
kubectl --context ohm-us-east-1 -n at-utility patch secret at-utility-secrets --type merge -p ('{"data":{"AT_EDGE_SHARED_SECRET":"' + $b64 + '"}}')
kubectl --context ohm-us-east-1 -n at-utility rollout restart deploy/gateway deploy/gateway-rs
```

(`gateway` reads `AT_EDGE_SHARED_SECRET`; `gateway-rs` reads the same key as
`AT_RS_EDGE_SECRET` via the manifest.)

## Cost target

| Item | Approx/mo |
|------|-----------|
| EKS control plane | $73 |
| 1× t3.medium node | $30 |
| Redis (1× t4g.small, pre-revenue slim) | ~$23 |
| Redis (2× t4g.small Multi-AZ, HA) | ~$46 |
| NLB + NAT + data | $40–60 |
| **Total (slim)** | **~$165–185** |
| **Total (HA Redis)** | **~$190–210** |

A mid-cycle bill around **~$100** with mesh/GA already gone is consistent with
this floor (partial month or credits) — it is **not** SNS email. Slim knobs
(not teardown): [COST_FREEZE.md](COST_FREEZE.md). Neon mirror / snapshots:
[NEON.md](NEON.md). Never re-apply `cache.r6g.large` until mesh returns.
