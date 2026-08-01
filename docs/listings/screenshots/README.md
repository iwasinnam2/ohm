# Listing screenshots

Capture PNG/GIF here before refreshing Marketplace / cursor.directory:

1. `mcp-tools.png` — Cursor MCP panel with ohm tools
2. `fetch-web.gif` — ohm_fetch_web on a public URL
3. `usage.png` — ohm_usage snapshot
4. `add-to-cursor.png` — billing success deeplink CTA

Keep files small (<1MB each). See [MARKETPLACE.md](MARKETPLACE.md) and [MARKETPLACE_AUDIT.md](../MARKETPLACE_AUDIT.md).

## Capture checklist (operator)

Until captures are committed, use this smoke as evidence of attachability:

```powershell
pip install -e ".[mcp]"
$env:OHM_API_KEY = "sk-at-…"   # from Checkout
$env:OHM_BASE_URL = "https://api.withohm.dev/v1"
# Attach mcp.json in Cursor, then exercise ohm_usage / ohm_fetch_web / ohm_chat
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey $env:OHM_API_KEY
```

Follow-up if Directory/Marketplace silent >10 days: marketplace-publishing@cursor.com with plugin `ohm`, repo URL, submission date.
