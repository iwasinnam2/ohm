# Stripe webhook on public API (post-DNS)

After `https://api.withohm.dev/health` returns edge OK (not `edge_pending`):

1. Stripe Dashboard → Developers → Webhooks → Add endpoint  
   URL: `https://api.withohm.dev/v1/stripe/webhook`  
   Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` (and any already used in [docs/STRIPE.md](../../docs/STRIPE.md)).
2. Copy signing secret → k8s secret `STRIPE_WEBHOOK_SECRET` (and Secrets Manager).
3. Test lifecycle:

```powershell
# issue tenant → checkout → cancel → expect 403 suspended
# see docs/STRIPE.md
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-dev -SkipOpenAI
```

NLB-only testing is insufficient — Stripe requires a public HTTPS hostname.
