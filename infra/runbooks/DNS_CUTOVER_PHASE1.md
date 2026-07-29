# Phase 1 DNS cutover — `api.withohm.dev` → NLB

**NLB hostname (record before GA):**

```text
a8a4fb2a5e7214a93bc86c9b79a4f3c6-da5bb54336e41479.elb.us-east-1.amazonaws.com
```

Also saved in [NLB_HOSTNAME.txt](NLB_HOSTNAME.txt).

## Verified (pre-DNS via TLS SNI / `-ResolveIp`)

- `external_smoke.ps1 -BaseUrl https://api.withohm.dev -SkipOpenAI -ResolveIp <NLB_IP>` → PASS
- Stripe endpoint `we_1TyTnN…` → `https://api.withohm.dev/v1/billing/webhook`
- `python scripts/stripe_public_lifecycle.py` with `OHM_RESOLVE_IP` → checkout webhook → chat → cancel → **403**

## Remaining operator step

GoDaddy still serves `api` → Vercel. Until the CNAME below is live, public clients and Stripe Dashboard delivery see `edge_pending` 503.

## GoDaddy (nameservers are Third Party)

1. Lower TTL on `api` to 60s (optional).
2. Delete CNAME `api` → `*.vercel-dns-*.com`.
3. Add CNAME `api` → `a8a4fb2a5e7214a93bc86c9b79a4f3c6-da5bb54336e41479.elb.us-east-1.amazonaws.com`
4. In Vercel project `site`: remove domain `api.withohm.dev` if listed.
5. Set Vercel env `API_EDGE_LIVE=1` on `site` and redeploy.
6. Smoke:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-dev -SkipOpenAI
```

## Known follow-ups

- Rust RESP client does not speak TLS yet; `AT_RS_REDIS` is fail-fast (`127.0.0.1:9`) so the edge proxies to Python for cache. Python uses `rediss://` reader/primary.
- Add TLS to `gateway-rs` RESP, then restore ElastiCache endpoints on `AT_RS_REDIS` / `AT_RS_REDIS_WRITE`.
