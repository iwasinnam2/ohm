# Go-live checklist (Section E)

Public product: **Ohm**. Hosts: `withohm.dev` (site), `api.withohm.dev` (API), `status.withohm.dev` (status).
Internal AWS/k8s names may still be `at-utility`. See [docs/BRAND.md](../../docs/BRAND.md).
API DNS handoff: [API_CUTOVER.md](API_CUTOVER.md).

## Before cutover

- [x] Buy root domain; hosts decided (`withohm.dev` / `api.withohm.dev` / `status.withohm.dev`)
- [ ] Section A `release_smoke` green three consecutive days on staging
- [ ] Section C public hostname serves miss/hit OpenAI from a second network ([API_CUTOVER.md](API_CUTOVER.md) Phase 1)
- [ ] Section D: `enable_edges=true`; two edge regions show local cache hits within lag budget (&lt;1s lab)
- [ ] Stripe test mode: Intermediate checkout ($0 seat + meters) → chat miss/hit/fetch → meter events + invoice preview → cancel → 403 ([docs/STRIPE.md](../../docs/STRIPE.md))
- [ ] Confirm `GET /v1/usage` includes `stripe_synced` after metered traffic
- [ ] Confirm daily fetch soft-cap (`AT_FREE_TIER_FETCH_CAP_DAY`) until `invoice.paid`
- [ ] Dashboard: Smart Retries 8/2 weeks + failed-payment emails; end action = cancel ([docs/STRIPE_DUNNING.md](../../docs/STRIPE_DUNNING.md))
- [ ] Delinquency smoke: `invoice.payment_failed` → fetch 402; after `AT_DELINQUENT_SUSPEND_DAYS` or cancel → 403
- [ ] OpenAI hard budget alert set (your ledger)
- [ ] AWS Budgets alarm set (infra ledger)
- [x] ACM certificate issued for `api.withohm.dev`; Terraform `domain_name` set
- [ ] Global Accelerator endpoints healthy on `/health` (`anycast_enabled=true` + NLB ARNs)
- [ ] Status page live (`status.withohm.dev` → site `/status`)
- [x] Marketing site (`site/`) deployed on apex; docs match hostname
- [x] Terms of service + DPA published
- [ ] On-call rotation / incident channel defined
- [ ] Record last-known-good NLB hostname before GA cutover

## Cutover

Follow [API_CUTOVER.md](API_CUTOVER.md): NLB first, then GA. Set Vercel `API_EDGE_LIVE=1` after DNS leaves Vercel.

1. Lower DNS TTL on `api.withohm.dev` to 60s (day before).
2. Attach regional NLBs to Global Accelerator; verify health checks.
3. Point `api.withohm.dev` to GA (CNAME to GA DNS name).
4. Run `external_smoke.ps1 -BaseUrl https://api.withohm.dev` from two networks / continents if possible.
5. Watch miss ratio, OpenAI error rate, regional latency p99 for 60 minutes.

## After cutover

- [ ] Restore normal DNS TTL
- [ ] Complete one region-drain drill ([REGION_DRAIN.md](REGION_DRAIN.md))
- [ ] Rotate any bootstrap keys that were used in demos
- [ ] File incident runbook link in the team wiki

## Abort

If OpenAI error rate spikes or GA health fails in &gt;1 region: revert DNS to last known good NLB, disable unhealthy GA endpoints, page on-call.
