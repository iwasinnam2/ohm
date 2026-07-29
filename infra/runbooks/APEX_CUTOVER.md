# Apex DNS cutover (withohm.dev → Vercel)

**Do not change nameservers.** Keep GoDaddy NS (`ns69` / `ns70.domaincontrol.com`) so Microsoft 365 MX/TXT stay intact.

Vercel project: `site` (domains attached: `withohm.dev`, `www.withohm.dev`, `api.withohm.dev`).

## GoDaddy → DNS → Add (only these)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **A** | `@` | `216.198.79.1` | 600 / 1 Hour |
| **A** | `@` | `64.29.17.1` | 600 / 1 Hour |
| **CNAME** | `www` | `01dad5366ab21a23.vercel-dns-017.com` | 600 / 1 Hour |

### Leave alone

- All **MX** records (Microsoft 365)
- M365 **TXT** (verification, DKIM `selector1` / `selector2` CNAMEs, autodiscover)
- Existing **ACM validation** CNAME under `api` if still present (`_….api`)
- Current **`api` CNAME** to Vercel until [API_CUTOVER.md](API_CUTOVER.md)

### SPF (outbound mail)

Apex **TXT** `@` SPF should authorize Outlook for `partners@withohm.dev`:

```text
v=spf1 include:spf.protection.outlook.com -all
```

If you still send via GoDaddy as well: `include:spf.protection.outlook.com include:secureserver.net`.

### Status host

| Type | Name | Value |
|------|------|-------|
| **CNAME** | `status` | `cname.vercel-dns.com` (or project `*.vercel-dns-017.com`) |

Attach `status.withohm.dev` in the Vercel `site` project (rewrites to `/status` via middleware).

## Verify

```powershell
npx vercel domains verify withohm.dev
npx vercel domains verify www.withohm.dev
curl.exe -sI https://withohm.dev
curl.exe -sI https://www.withohm.dev
curl.exe -s https://api.withohm.dev/health
# expect 503 JSON edge_pending until AWS API cutover
```

## After HTTPS is green on apex

1. Prefer sharing `https://withohm.dev` as the public site.
2. Keep `api.withohm.dev` for NLB/GA — see [API_CUTOVER.md](API_CUTOVER.md) (ACM already issued).
3. Confirm `partners@withohm.dev` mailbox exists in M365.
4. Attach `status.withohm.dev` and verify https://status.withohm.dev.