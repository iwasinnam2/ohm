# Single-region posture (Jul 2026)

withOhm serves all traffic from **us-east-1**: EKS (`at-utility-eks`, 1×
t3.medium) running `gateway` (Python control plane), `gateway-rs` (Rust edge),
and `ingest-worker`, in front of ElastiCache Redis (`at-utility-redis-leader`,
2 nodes, multi-AZ, TLS, **daily snapshots, 7-day retention**). The mesh
(us-west-2 + eu-west-2 edges, Global Datastore, Global Accelerator) was torn
down to cut burn from ~$1.5–2k/mo toward <$200/mo. Terraform keeps the mesh
behind `enable_edges` / `anycast_enabled` for when paid traffic justifies it.

## Region notes

- `AT_REGION` stays `us-east-1` on the leader. Setting it to an edge region
  name on a pod that writes through to Redis will mis-route cache-key metadata
  — only set it when a real edge deployment returns (this note used to live in
  `infra/k8s/manifests.yaml`).
- Redis GET/SET both land on the leader replication group (reader + primary
  endpoints). No Global Datastore.

## Teardown state (check before re-running)

Done:

- eu-west-2: k8s namespace deleted (NLB released), full edge stack destroyed
  via `terraform apply -target=module.edge_eu_west_2`.
- Leader manifests: liveness probes, `/ready` readiness on gateway, edge-hit
  secret wiring, images `0.1.9`.
- Leader Redis: snapshot retention 7d staged in Terraform.

Blocked on us-west-2 network reachability from the operator machine (TCP 443
to all us-west-2 endpoints blackholed at time of teardown; the Global
Accelerator API is also homed in us-west-2):

```powershell
# 1. Confirm reachability
Test-NetConnection eks.us-west-2.amazonaws.com -Port 443
# 2. Release the us-west-2 NLB (k8s-owned, outside Terraform)
kubectl --context ohm-us-west-2 delete namespace at-utility --wait=false
# 3. Finish the teardown + right-size (destroys us-west-2 stack, Global
#    Datastore, Global Accelerator; scales leader node group to 1)
cd infra/terraform
terraform plan -out=teardown.tfplan   # review: only us-west-2/GD/GA destroys
terraform apply teardown.tfplan
# 4. After the GD is gone, flip redis_node_type = "cache.t4g.small" in
#    terraform.tfvars (t-family is GD-incompatible; usage is ~11 MB) and apply.
# 5. Remove the temporary skip_credentials_validation block from the
#    us_west_2 provider in edges.tf.
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
| Redis (2× t4g.small, after flip) | $46 |
| NLB + NAT + data | $40–60 |
| **Total** | **~$190–210** |
