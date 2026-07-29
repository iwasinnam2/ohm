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

Attach once via MCP and get:
• ohm_chat — OpenAI-compatible chat through Ohm’s pipe (Redis prompt replay)
• ohm_fetch_web — purpose-bound public URL scrape → markdown or JSON for agents
• ohm_usage — cache hits, fetches, and estimated pipe rent

You bring the provider key (BYOK). Ohm rents the plumbing — not wholesale tokens.

Getting started
1. Create a seat at https://withohm.dev/subscriptions (trial / Intermediate $0 membership + meters)
2. On the success screen, click Add withOhm to Cursor (one-click MCP install)
3. Or apply as a founding design partner (90-day complimentary): https://withohm.dev/design-partners

Docs: https://withohm.dev/docs/cursor
Discovery notes: https://github.com/iwasinnam2/ohm/blob/master/docs/CURSOR_DISCOVERY.md
API: https://api.withohm.dev/v1
Support: partners@withohm.dev
```

## Keywords

`ohm`, `withohm`, `withOhm`, `mcp`, `prompt-cache`, `web-fetch`, `web-scrape`, `byok`, `openai-compatible`, `agent-browse`, `url-context`

## Logo

`https://withohm.dev/ohm-icon-360.png` (or in-repo `assets/logo.svg`)

## Homepage / repo

- https://withohm.dev
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
