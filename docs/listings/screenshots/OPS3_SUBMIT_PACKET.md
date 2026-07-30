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
A record deleted. Domain Forward still needs GoDaddy login (verify_apex.ps1).
