# Phase 2 DNS — api.withohm.dev → Global Accelerator

**Abort target (NLB):** see [NLB_HOSTNAME.txt](NLB_HOSTNAME.txt)

**GA DNS:**

```text
a8d1c391c281079a4.awsglobalaccelerator.com
```

**Anycast IPs:** `15.197.180.160`, `3.33.246.129`

## GoDaddy

1. Edit CNAME `api` → `a8d1c391c281079a4.awsglobalaccelerator.com` (replace NLB target).
2. Keep TTL low until smoke is green.
3. Smoke:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-dev -SkipOpenAI
```

Pre-DNS verify (SNI):

```powershell
$ip = (Resolve-DnsName a8d1c391c281079a4.awsglobalaccelerator.com -Type A)[0].IPAddress
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-dev -SkipOpenAI -ResolveIp $ip
```
