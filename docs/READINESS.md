# Readiness — suspension bridge before traffic

Public distribution readiness for **Ohm**. Towers can be walked; the roadway is not open until the deck is complete.

## Verdict

| Layer | Status |
|-------|--------|
| Marketing / legal (`withohm.dev`) | Standing |
| Local edge (`:8081`) + railgun smoke | Standing |
| Stripe seat Checkout (test) | Standing |
| Cursor deeplink CTA | Standing |
| Public GitHub origin | Required for marketplace |
| Valid logotype SVG/PNG | Required for marketplace |
| Public API deck (`api.withohm.dev`) | **Not open** — see GO_LIVE |
| Multi-region / Anycast | Deferred |

**Allow global traffic** only after public chat miss/hit on `https://api.withohm.dev`, Stripe lifecycle green on that host, and a public repo for trust + Cursor submit.

## Immediate (this pass)

- [x] ASCII-safe logo: [`brand/ohm-icon.svg`](../brand/ohm-icon.svg), [`site/public/ohm-icon.svg`](../site/public/ohm-icon.svg), [`assets/logo.svg`](../assets/logo.svg)
- [x] PNG: [`brand/ohm-icon-360.png`](../brand/ohm-icon-360.png) → `https://withohm.dev/ohm-icon-360.png` after site deploy
- [x] Cursor plugin shape: [`.cursor-plugin/plugin.json`](../.cursor-plugin/plugin.json) + [`mcp.json`](../mcp.json)
- [ ] Public GitHub push (repo URL for marketplace “global repo link”)

Logotype URLs for Cursor submit:

- Prefer PNG: `https://withohm.dev/ohm-icon-360.png`
- Or SVG: `https://withohm.dev/ohm-icon.svg`
- Or relative in-repo: `assets/logo.svg`

## Deck before traffic (from [GO_LIVE.md](../infra/runbooks/GO_LIVE.md))

- [ ] `release_smoke` green on staging (consecutive days as required)
- [ ] [API_CUTOVER.md](../infra/runbooks/API_CUTOVER.md) Phase 1+ — NLB then GA for `api.withohm.dev`
- [ ] `external_smoke.ps1 -BaseUrl https://api.withohm.dev` from a second network
- [ ] Vercel `API_EDGE_LIVE=1` after DNS leaves edge-pending
- [ ] Stripe webhook against public API; checkout → cancel → 403
- [ ] OpenAI + AWS budget alerts
- [ ] On-call / incident channel
- [ ] Status page: `status.withohm.dev`

## After first traffic

- [ ] Tag `v0.1.0-railgun`
- [ ] Cursor Marketplace submit: https://cursor.com/marketplace/publish
- [ ] SDK publish ([PLATFORM.md](PLATFORM.md)) only after public smoke
- [ ] Design-partner quotes on homepage

## Deferred (do not claim yet)

- Mid-stream failover
- Multi-region Redis lag / Anycast
- Enterprise contractual SLA
- Managed-key capacity pools
- Hosted remote MCP URL (zero `pip install`)
