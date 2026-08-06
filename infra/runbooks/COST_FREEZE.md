# AWS cost freeze (pre-revenue)

You are not being robbed by email. SNS email is cents. A ~**$100–210/mo**
bill with the current single-region API up is the EKS + Redis + NAT + NLB
floor. Mesh used to be **$1.5–2k/mo**; that is already torn down.

## Where the money goes (us-east-1, API live)

| Line | Approx/mo | Required for `api.withohm.dev`? |
|------|-----------|----------------------------------|
| EKS control plane | ~$73 | Yes while cluster exists |
| 1× `t3.medium` node | ~$30 | Yes (pods need a node) |
| Redis 2× `cache.t4g.small` Multi-AZ | ~$46 | Yes (hot path) |
| NAT Gateway + EIP + data | ~$33+ | Yes with current private nodes |
| NLB | ~$16–25 | Yes (public edge) |
| Route53 health checks ×2 | ~$1–4 | No (alarms only) |
| Amplify (`www` / `fetch` / `status`) | low tens | Marketing only |
| Global Accelerator | **$0 if destroyed** | No — DNS should hit NLB |
| Edge mesh (`enable_edges`) | **$0 if false** | No |

Documented target with API up: **~$190–210/mo**
([SINGLE_REGION.md](SINGLE_REGION.md)). A **~$106** month is already leaner
than that table (partial month, credits, or GA already gone) — open **Cost
Explorer → Group by Service** before cutting further so you kill the real line.

Neon Postgres is a **separate** Neon invoice, not this AWS account.

## Already off — do not turn back on

- `enable_edges = false` (two more EKS + NAT + Redis regions)
- `anycast_enabled = false` (Global Accelerator)
- SNS email paused — [EMAIL_ALERTS.md](EMAIL_ALERTS.md) / PR for mailbox only (~$0)

## Footguns that recreate a fat bill

- Applying with `redis_node_type = cache.r6g.large` (old example default) →
  Redis alone ~$360+/mo. Repo default is now `cache.t4g.small`.
- `eks_desired_nodes = 2` → second node. Default is now `1`.
- Setting `enable_edges = true` without paid traffic.

## Soft cuts (API stays up)

1. Cost Explorer → confirm no `AWSGlobalAccelerator` / leftover edge regions.
   If GA still exists after DNS → NLB, destroy it (`anycast_enabled=false` apply).
2. Amplify: disable PR/feature-branch apps; keep `master` only.
3. Unsubscribe SNS email (pennies; still do it — [EMAIL_ALERTS.md](EMAIL_ALERTS.md)).
4. Delete Route53 health checks + alarms if you do not care about AWS uptime
   mail/Slack (small $).

## Hard freeze (API goes dark — real savings)

Only when you accept `api.withohm.dev` being down until revive:

```powershell
# Scale workers to zero (EKS control plane STILL bills ~$73)
aws eks update-nodegroup-config --cluster-name at-utility-eks `
  --nodegroup-name <nodegroup> --scaling-config minSize=0,maxSize=1,desiredSize=0 `
  --region us-east-1
```

To drop most of the bill you must **destroy** (painful revive):

1. Scale node group desired/min → 0, drain workloads.
2. `enable_eks = false` → apply (drops ~$73 CP + node).
3. Destroy Redis replication group + NAT + NLB (Terraform or console).
4. Leave Amplify up if you still want the marketing site.

There is no scale-to-zero path that keeps the live API: HPA minReplicas=1,
node group min=1, EKS CP always-on.

## Resume after revenue

1. Keep `redis_node_type = cache.t4g.small`, `eks_desired_nodes = 1`,
   `enable_edges = false`, `anycast_enabled = false`.
2. Re-apply / re-create EKS + Redis + NAT only when you need the API.
3. Mesh / GA / `r6g.large` only after paid traffic justifies [MESH_PHASE3_5.md](MESH_PHASE3_5.md).
