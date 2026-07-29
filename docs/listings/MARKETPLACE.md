# Cursor Marketplace listing draft

Paste / adapt into https://cursor.com/marketplace/publish

## Name

`ohm` (withOhm)

## Short description (≤160 chars)

```
BYOK model ingress for Cursor: prompt cache replay, compliant web fetch, usage meters. Change one attach — keep your keys.
```

## Long description

```
withOhm is an AI traffic utility for Cursor.

Attach once via MCP and get:
• ohm_chat — OpenAI-compatible chat through Ohm’s pipe (Redis prompt replay on identical prompts)
• ohm_fetch_web — purpose-bound public URL scrape → markdown or JSON for agents
• ohm_usage — cache hits, fetches, and estimated pipe rent

You bring the provider key (BYOK). Ohm rents the plumbing — not wholesale tokens.

Getting started
1. Create a seat at https://withohm.dev/subscriptions (trial / Intermediate $0 membership + meters)
2. On the success screen, click Add withOhm to Cursor (one-click MCP install)
3. Or apply as a founding design partner (90-day complimentary): https://withohm.dev/design-partners

Docs: https://withohm.dev/docs/cursor
API: https://api.withohm.dev/v1
Support: partners@withohm.dev
```

## Keywords

`mcp`, `ohm`, `cache`, `web-fetch`, `byok`, `openai-compatible`, `prompt-cache`

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
