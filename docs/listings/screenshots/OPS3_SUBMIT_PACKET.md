# Marketplace submit packet (Ops 3) — 2026-07-30

## Verified live before submit
- Logo https://www.withohm.dev/ohm-icon-360.png → 200
- Status https://www.withohm.dev/status → Amplify + live API (no Vercel/edge_pending)
- Subscriptions → Intermediate + Enterprise only (no 30-day trial / managed keys)
- API https://api.withohm.dev/health → rust; /ready → python redis ok (sanitized)
- Images rolled: gateway/ingest 0.1.7, gateway-rs 0.1.8 (all regions)

## Paste into https://cursor.com/marketplace/publish
See MARKETPLACE.md (short + long). Repo: https://github.com/iwasinnam2/ohm License: MIT

## cursor.directory
See CURSOR_DIRECTORY.md

## Screenshots still needing Cursor UI (operator)
- mcp-tools.png, fetch-web.png, usage.png, add-to-cursor.png
Web evidence: ohm-icon-360.png committed; /i and /status captured in browser session.

## Apex

| Step | Status |
|------|--------|
| Delete Vercel A on `@` | **Done** (no A record; NXDOMAIN) |
| Domain Forward / ALIAS → www | **Needs GoDaddy login** — `scripts/verify_apex.ps1` |

## Marketplace / directory

| Step | Status |
|------|--------|
| Evidence packet + logo + `/i` screenshot | **Done** in `docs/listings/screenshots/` |
| Paste refresh at cursor.com/marketplace/publish | **Needs Cursor account login** |
| cursor.directory update | **Needs account** — copy in CURSOR_DIRECTORY.md |
| Cursor IDE mcp/fetch/usage screenshots | **Needs live seat key in IDE** |
