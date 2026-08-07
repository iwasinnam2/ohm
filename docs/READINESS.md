# Readiness — marketplace pre-approval window

Public distribution readiness for **withOhm** (Ohm). Hosted pipe is live; this checklist tracks Cursor Marketplace review readiness.

## Verdict (live)

| Layer | Status |
|-------|--------|
| Marketing / legal (`www.withohm.dev`) | Live — AWS Amplify + CloudFront |
| Public API (`api.withohm.dev`) | Live — EKS, single-region us-east-1 |
| Fetch toy (`fetch.withohm.dev`) | Live — demo strip (not full compliance pipe) |
| Stripe seat Checkout + meters | Live |
| Cursor deeplink CTA | Live |
| Public GitHub | https://github.com/iwasinnam2/ohm |
| Logotype PNG/SVG | In-repo + `site/public/ohm-icon-360.png` |
| Repo LICENSE | MIT (matches plugin.json) |
| Local stdio MCP | Shipped |
| Remote MCP (stateless streamable HTTP) | Shipped in-repo (`ohm-mcp-http`); hosted `mcp.withohm.dev` endpoint is operator follow-up |
| Apex `withohm.dev` | Prefer **www** until GoDaddy 301 cutover |

## Marketplace blockers cleared (this sprint)

- [x] MIT LICENSE + NOTICE
- [x] Logo PNG in `site/public/`
- [x] Public surfaces truth (Amplify marketing + live API; status UI retired)
- [x] False claims removed (managed keys / 30-day trial)
- [x] MCP: no forged legal acks; `OHM_API_KEY` required
- [x] SSRF DNS re-check; robots fail-closed
- [x] Checkout mint rate limit; Rust Redis auth errors → **Unverified** full-proxy (Python still authz); `/ready` sanitized
- [x] Ingest NetworkPolicy; `request_cap` enforced
- [x] Fetch toy labeled demo vs Ohm pipe
- [x] Self-audit: [listings/MARKETPLACE_AUDIT.md](listings/MARKETPLACE_AUDIT.md)

## Still operator / follow-up

- [ ] GoDaddy apex → www ([APEX_CUTOVER.md](../infra/runbooks/APEX_CUTOVER.md))
- [ ] Amplify redeploy so `www` serves new PNG + status + copy
- [ ] Gateway/edge image roll with compliance + auth hardening
- [ ] Cursor Marketplace submit / refresh: [listings/MARKETPLACE.md](listings/MARKETPLACE.md)
- [ ] cursor.directory: [listings/CURSOR_DIRECTORY.md](listings/CURSOR_DIRECTORY.md)
- [ ] Screenshots in [listings/screenshots/](listings/screenshots/)
- [ ] Design-partner quotes on homepage (inbound via [/design-partners](https://www.withohm.dev/design-partners))
- [ ] Host remote MCP at `mcp.withohm.dev` (`OHM_MCP_TRANSPORT=http ohm-mcp`, stateless; per-request `Authorization: Bearer sk-at-*`)
- [ ] Set signing seeds + register OhmBot with Cloudflare Verified Bots — full runbook: [infra/runbooks/VERIFIED_BOT.md](../infra/runbooks/VERIFIED_BOT.md)

## Deferred (do not claim)

- Mid-stream failover (pre-first-byte retry **is** shipped; handoff after first byte is not)
- Enterprise contractual SLA
- Managed-key capacity pools
- Tokyo (`ap-northeast-1`) edge (optional third region)
- Full package/key rename away from `at-utility` / `sk-at-*`
