# API cutover (`api.withohm.dev` → AWS)

Moves chat traffic off Vercel `edge_pending` onto the Ohm edge (NLB, then Global Accelerator).

Keep GoDaddy nameservers. Do **not** touch MX / M365 / ACM validation CNAMEs for `_….api`.

## Prerequisites

1. Section C: leader stack applied; ECR images pushed (`infra/scripts/ecr_push.sh`).
2. EKS (or compatible) cluster; `infra/scripts/k8s_deploy.sh` applied; `gateway-rs` Service has an NLB hostname.
3. ACM certificate **ISSUED** for `api.withohm.dev`; ARN set on the NLB TLS annotation.
4. `external_smoke.ps1 -BaseUrl https://<nlb-host>` green from a second network (use Host header or temp DNS).
5. Stripe test lifecycle green (optional for first chat traffic; required before paid tenants).
6. Set Vercel env `API_EDGE_LIVE=1` on project `site` **after** DNS points at AWS (retires middleware 503).

## Capture last-known-good NLB

```powershell
kubectl -n at-utility get svc gateway-rs -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; Write-Host
# Record: NLB_HOSTNAME=...
# terraform output acm_certificate_arn
```

Abort target = this NLB hostname until GA is proven.

## Phase 1 — NLB DNS (Section C exit)

1. Lower TTL on `api` CNAME to 60s (day before).
2. In GoDaddy DNS for `withohm.dev`:
   - **Delete** CNAME `api` → `*.vercel-dns-*.com` (Vercel).
   - **Add** CNAME `api` → `<NLB_HOSTNAME>` (AWS NLB DNS name, trailing dot OK).
3. In Vercel: remove domain `api.withohm.dev` from project `site` (stops marketing/edge-pending on that host).
4. Set `API_EDGE_LIVE=1` on the marketing project and redeploy (banner + middleware).
5. Wait for propagation; run:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev
```

Expect `/health` 200 from the edge, not `edge_pending` 503.

## Phase 2 — Global Accelerator (Section E)

1. Set `anycast_enabled = true` and `ga_nlb_endpoint_arns` in `infra/terraform/terraform.tfvars`.
2. `terraform apply` — creates accelerator, listener, endpoint group.
3. Health: GA endpoints healthy on TCP/443 → `/health`.
4. Point CNAME `api` → GA DNS name (`terraform output global_accelerator`).
5. Smoke from two networks/continents; watch miss ratio and upstream errors 60 minutes.
6. Restore normal DNS TTL.

## Abort

If OpenAI error rate spikes or GA health fails: point `api` CNAME back to recorded **NLB** hostname; disable unhealthy GA endpoints; page on-call.

## Related

- [GO_LIVE.md](GO_LIVE.md) — full checklist
- [APEX_CUTOVER.md](APEX_CUTOVER.md) — marketing apex only (leave alone during API cutover)
- [REGION_DRAIN.md](REGION_DRAIN.md) — post-cutover edge drain drill
