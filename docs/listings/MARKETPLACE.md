# Cursor Marketplace listing draft

Paste / adapt into https://cursor.com/marketplace/publish

## Name

`ohm` (withOhm)

## Short description (≤160 chars)

```
withOhm (ohm): BYOK Cursor MCP — prompt cache replay, compliant web fetch, OpenAI-compatible ingress.
```

## Long description

```
withOhm is an AI traffic utility for Cursor (search: ohm, withOhm, prompt-cache, web-fetch).

Attach once via local stdio MCP (pip install at-utility[mcp]) and get:
• ohm_chat — OpenAI-compatible chat through Ohm’s pipe (Redis prompt replay)
• ohm_fetch_web — purpose-bound public URL scrape → markdown or JSON for agents
• ohm_usage — cache hits, fetches, and estimated pipe rent

You bring the provider key (BYOK). Ohm rents the plumbing — not wholesale tokens.
License: MIT (open-source plugin + gateway). Hosted pipe is metered.

Getting started
1. Create an Intermediate seat at https://www.withohm.dev/subscriptions ($0 membership + meters, card on file)
2. On the success screen, click Add withOhm to Cursor (one-click MCP install)
3. Or apply as a founding design partner (90-day complimentary): https://www.withohm.dev/design-partners

Docs: https://www.withohm.dev/docs/cursor
Privacy: https://www.withohm.dev/docs/privacy
Discovery notes: https://github.com/iwasinnam2/ohm/blob/master/docs/CURSOR_DISCOVERY.md
API: https://api.withohm.dev/v1
Support: partners@withohm.dev
```

## Keywords

`ohm`, `withohm`, `withOhm`, `mcp`, `prompt-cache`, `web-fetch`, `web-scrape`, `byok`, `openai-compatible`, `agent-browse`, `url-context`, `compliant-fetch-for-agents`

## Publish / refresh

1. https://cursor.com/marketplace/publish — paste short + long description above; logo `https://www.withohm.dev/ohm-icon-360.png`
2. cursor.directory — [CURSOR_DIRECTORY.md](CURSOR_DIRECTORY.md)
3. One-liner everywhere: `Add withOhm MCP from https://www.withohm.dev/i`

## Logo

Prefer `https://www.withohm.dev/ohm-icon-360.png` (or in-repo `assets/logo.svg`)

## Homepage / repo

- https://www.withohm.dev
- https://github.com/iwasinnam2/ohm

## Screenshots to capture (do before submit refresh)

1. Cursor MCP panel with `ohm` tools listed
2. Agent calling `ohm_fetch_web` on a public docs URL
3. `ohm_usage` showing hit ratio + fetches
4. withohm.dev billing success “Add to Cursor” button

Store under `docs/listings/screenshots/` when ready (git-lfs or compressed PNG).

## Config defaults (plugin)

`OHM_BASE_URL` default: `https://api.withohm.dev/v1`  
Required: `OHM_API_KEY`  
Optional: `OHM_UPSTREAM_KEY`

Remote URL MCP is **not** shipped — local stdio only.
