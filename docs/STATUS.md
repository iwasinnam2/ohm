# Status and limits

## Service status

| Surface | URL | State |
|---------|-----|--------|
| Docs / marketing | https://www.withohm.dev | Live (AWS Amplify + CloudFront) |
| Status page | https://status.withohm.dev → `/status` | Live |
| Public API | https://api.withohm.dev | Live (EKS + Global Accelerator) |
| Fetch toy | https://fetch.withohm.dev | Live (demo strip) |
| Local MVP edge | http://localhost:8081 | Supported for local smoke |

```powershell
.\scripts\release_smoke.ps1
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-...
```

## Hosts

| Host | Role |
|------|------|
| `www.withohm.dev` | Marketing + docs (prefer until apex 301) |
| `withohm.dev` | Apex — forward to www per [APEX_CUTOVER.md](../infra/runbooks/APEX_CUTOVER.md) |
| `api.withohm.dev` | Public API |
| `fetch.withohm.dev` | Public fetch demo |
| `status.withohm.dev` | Status page |

See [BRAND.md](BRAND.md) and [infra/runbooks/GO_LIVE.md](../infra/runbooks/GO_LIVE.md).

## Current limits (defaults)

| Limit | Default | Env |
|-------|---------|-----|
| Rate (requests/sec) | 20 | `AT_RATE_LIMIT_RPS` |
| Burst | 40 | `AT_RATE_LIMIT_BURST` |
| Cache TTL | 3600s | `AT_CACHE_TTL_SECONDS` |
| Mid-stream failover | Unsupported | see [STREAMING.md](STREAMING.md) |
| Enterprise contractual SLA | Not published (MVP) | SKU `sla` is null |

## Regions (target topology)

| Role | Region |
|------|--------|
| Leader | `us-east-1` |
| Edges | `us-west-2`, `eu-west-2`, `ap-northeast-1` (`enable_edges=true`) |

Local Docker reports `AT_REGION=local`.

## What is cached

Prompt + response payloads for identical requests (tenant-scoped cache keys). See [SECURITY.md](SECURITY.md) for retention and opt-out.

## Compliance limits (web ingest)

| Control | Default |
|---------|---------|
| Enforcement | On (`AT_COMPLIANCE_ENFORCE`) |
| Allowed purposes | `public_web_retrieval`, `business_catalog`, `public_company_info`, `job_listings` |
| Lead harvest / dossiers / biometrics / gated access / PECR cold outreach | Rejected |
| Terms / DPA ack | Required for web context + tenant issue |
| Excerpt caps | 4000/source, 12000 total |
| Cache training export | Hard-denied |
| `cache_control: no_store` | Skips Redis write |
| robots.txt | Respected (fail-closed on fetch errors) |
| PII redaction in fetched markdown | On |
| DNS rebind / private IP after resolve | Denied |
