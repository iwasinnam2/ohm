# Marketplace self-audit checklist

Pre-flight for Cursor Marketplace review (manual security + quality).  
Repo: https://github.com/iwasinnam2/ohm · Plugin: `ohm` / withOhm

## Open source & packaging

- [x] Root [`LICENSE`](../../LICENSE) is MIT (matches `.cursor-plugin/plugin.json`)
- [x] [`NOTICE`](../../NOTICE) clarifies hosted pipe is commercial
- [x] No committed secrets (`.env` gitignored; `.env.example` placeholders)
- [x] Plugin ships markdown/skills + stdio MCP — no binaries in package surface
- [x] Manifest: [`.cursor-plugin/plugin.json`](../../.cursor-plugin/plugin.json) · [`mcp.json`](../../mcp.json) · [`skills/`](../../skills/)

## Install honesty

- [x] Local stdio MCP only (remote URL MCP deferred)
- [x] `OHM_API_KEY` required — no `sk-at-dev` production default
- [x] Default `OHM_BASE_URL` = `https://api.withohm.dev/v1`
- [x] Install: `pip install -e ".[mcp]"` or `pip install "at-utility[mcp] @ git+https://github.com/iwasinnam2/ohm.git"`
- [x] Legal acks bound at Checkout / tenant mint — MCP does not forge `terms_ack` / `dpa_ack`

## Security / compliance (reviewer hot paths)

- [x] URL gate: scheme, credentials, private literals, metadata host, **DNS resolve re-check**
- [x] robots.txt: **fail-closed** on fetch errors; 404 still allows
- [x] Unauthenticated checkout: IP token-bucket rate limit
- [x] Rust edge: **fail-closed** when Redis auth lookup errors
- [x] Prod `/ready`: no Redis exception strings / internal host dump
- [x] Ingest NetworkPolicy: ClusterIP peers only (`infra/k8s/manifests.yaml`)
- [x] `request_cap` enforced in `auth_tenant`
- [x] Prod ConfigMap: `AT_COMPLIANCE_ENFORCE=true`, `AT_BYOK_ALLOW_ENV_FALLBACK=false`
- [x] Public fetch toy labeled **demo** (not “compliant pipe”) when `via=toy`

## Product claims

- [x] Intermediate = `$0 membership + meters + BYOK` (API plan id `payg`)
- [x] No “30-day free trial” / “proxy-managed keys” on Intermediate
- [x] Status page: Amplify + live API (not Vercel / edge_pending)
- [x] Share line prefers `https://www.withohm.dev/i` until apex 301

## Legal links (listing)

- Privacy: https://www.withohm.dev/docs/privacy
- Terms: https://www.withohm.dev/docs/terms
- Security: https://www.withohm.dev/docs/security
- Ack versions: `tos-2026-07-26` / `dpa-2026-07-26`

## Evidence before refresh

1. Screenshots under [`screenshots/`](screenshots/) (MCP tools, fetch, usage, billing CTA)
2. `.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev`
3. Cold MCP: install from git, set `OHM_API_KEY`, call three tools
4. Refresh https://cursor.com/marketplace/publish with [`MARKETPLACE.md`](MARKETPLACE.md)
5. Update https://cursor.directory per [`CURSOR_DIRECTORY.md`](CURSOR_DIRECTORY.md)
6. If silent >10 days: email marketplace@cursor.com

## User DNS (outside repo)

- [ ] GoDaddy apex: delete Vercel A; 301 `@` → `https://www.withohm.dev` ([APEX_CUTOVER.md](../../infra/runbooks/APEX_CUTOVER.md))
