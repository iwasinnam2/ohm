# Marketplace follow-up (Days 11–14)

## Refresh submit

1. Open https://cursor.com/marketplace/publish
2. Paste copy from [MARKETPLACE.md](MARKETPLACE.md)
3. Logo: `https://www.withohm.dev/ohm-icon-360.png` (after Amplify deploy) or repo `assets/logo.svg`
4. Repo: https://github.com/iwasinnam2/ohm
5. Confirm MIT + privacy link https://www.withohm.dev/docs/privacy

## cursor.directory

Submit / update using [CURSOR_DIRECTORY.md](CURSOR_DIRECTORY.md).

## Smoke evidence

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey $env:OHM_API_KEY
pip install -e ".[mcp]"
# Cursor MCP attach with OHM_API_KEY — exercise ohm_usage, ohm_fetch_web, ohm_chat
```

Self-audit: [MARKETPLACE_AUDIT.md](MARKETPLACE_AUDIT.md)

## Email if silent >10 days

To: marketplace@cursor.com  
Subject: withOhm (ohm) plugin — review status

```
Hi Cursor Marketplace team,

Plugin: ohm (displayName withOhm)
Repo: https://github.com/iwasinnam2/ohm
Homepage: https://www.withohm.dev
Submitted / refreshed: <DATE>

Could you confirm queue status or any blockers? Happy to provide a test seat key.

Thanks,
partners@withohm.dev
```

Optional: forum bump https://forum.cursor.com (do not claim first-party placement).

## Smoke (this sprint)

- `GET https://api.withohm.dev/health` → 200 `plane=rust` (verified)
- MCP `_cfg()` requires `OHM_API_KEY` (verified)
- `pytest tests/test_compliance.py` → 18 passed
- Full `external_smoke.ps1` needs a live seat key — run when refreshing submit

## Screenshots

Operator capture into [screenshots/](screenshots/) — checklist in README / CAPTURE_LOG there.

