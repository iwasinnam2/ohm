# Apex DNS cutover (withohm.dev → Amplify)

**Do not change nameservers.** Keep GoDaddy NS (`ns69` / `ns70.domaincontrol.com`) so Microsoft 365 MX/TXT stay intact.

Amplify app: `withohm-site` (`d136djyswic57f`) · branch `cursor/mesh-phase3-5-prod`  
CloudFront target: `d2pta05dql0ixa.cloudfront.net`

## GoDaddy → DNS → Manage (replace Vercel site records)

### 1) ACM cert validation (required first)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **CNAME** | `_b2c27dc90a5aae0a5ed551e27f7c9d9e` | `_0f57ecf208c71a4b12bad60fa8404bf8.jkddzztszm.acm-validations.aws.` | 600 |

### 2) Site hosts → Amplify

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **CNAME** | `www` | `d2pta05dql0ixa.cloudfront.net` | 600 |
| **CNAME** | `fetch` | `d2pta05dql0ixa.cloudfront.net` | 600 |
| **CNAME** | `status` | `d2pta05dql0ixa.cloudfront.net` | 600 |

**Apex `@`:** GoDaddy often blocks CNAME on `@`. Prefer one of:

1. **Domain Forward** `withohm.dev` → `https://www.withohm.dev` (301), **or**
2. If GoDaddy offers **ALIAS / ANAME** on `@`, point it at `d2pta05dql0ixa.cloudfront.net`, **or**
3. Delete the old Vercel **A** records on `@` (`216.198.79.1`, `64.29.17.1`) once www is green, then use Amplify’s apex guidance in Console if they expose IPs.

### Remove (site only — do not touch API/mail)

| Type | Name | Old value (remove) |
|------|------|--------------------|
| **A** | `@` | Vercel `216.198.79.1` / `64.29.17.1` (after www works) |
| **CNAME** | `www` | `*.vercel-dns-*.com` |
| **CNAME** | `status` | old Vercel target |

### Leave alone

- All **MX** (Microsoft 365)
- M365 **TXT** / DKIM / autodiscover
- **`api` CNAME** → NLB / GA ([API_CUTOVER.md](API_CUTOVER.md))
- Existing **`api` ACM** validation CNAME if present

### SPF

```text
v=spf1 include:spf.protection.outlook.com -all
```

## Subdomains after cutover

| Host | Role |
|------|------|
| `https://withohm.dev` / `www` | Marketing + `/i` |
| `https://fetch.withohm.dev` | Public fetch toy (middleware → `/fetch`) |
| `https://status.withohm.dev` | Status |
| `https://api.withohm.dev` | API edge (unchanged — AWS NLB/GA) |

## Status (2026-07-29)

| Host | DNS | Serving |
|------|-----|---------|
| `www.withohm.dev` | CNAME → Amplify CloudFront | **Amplify** (200, `/i` live) |
| `fetch.withohm.dev` | CNAME → Amplify CloudFront | **Amplify** (200, fetch toy) |
| `status.withohm.dev` | CNAME → Amplify CloudFront | **Amplify** (200) |
| `withohm.dev` (apex) | **A** still `76.76.21.21` (Vercel IP) | **404 DEPLOYMENT_NOT_FOUND** after domain removed from Vercel project |
| `api.withohm.dev` | AWS GA | Unchanged / healthy |

Amplify domain association: **AVAILABLE** (`www` / `fetch` / `status` verified). Apex subdomain still `verified: false` until `@` stops using the Vercel A record.

Vercel project `site` no longer owns `withohm.dev` (removed from account).

### Finish apex NOW (GoDaddy — 2 minutes)

Apex is broken until you do this:

1. **Delete** the apex **A** record (`76.76.21.21` / any Vercel A).
2. **Domain Forward:** `withohm.dev` → `https://www.withohm.dev` (301 permanent), **or** ALIAS/ANAME `@` → `d2pta05dql0ixa.cloudfront.net` if GoDaddy offers it.
3. Confirm SNS email for AWS budget (`admin@withohm.dev`) if you have a pending subscription mail.

Until then, share **`https://www.withohm.dev`** and **`https://fetch.withohm.dev`**.
