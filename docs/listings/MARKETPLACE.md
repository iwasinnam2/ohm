# Cursor Marketplace listing draft

Paste / adapt into https://cursor.com/marketplace/publish

**Reviewer note (Cursor employees):** this refresh positions withOhm as the
metered pipe that cuts **repeat agent prefill waste** — exact-match Redis
replay + compliant web fetch — without touching Cursor model billing. Full
plan for employee review:  
https://github.com/iwasinnam2/ohm/blob/master/docs/GEM_POSITION.md  
BD one-pager:  
https://github.com/iwasinnam2/ohm/blob/master/docs/distribution/CURSOR_BD_BRIEF.md

## Name

`ohm` (withOhm)

## Short description (≤160 chars)

```
withOhm: cut repeat agent prefill waste — Redis prompt replay, BYOK pipe, compliant web fetch for Cursor.
```

## Long description

```
withOhm is an AI traffic utility for Cursor agents (search: ohm, withOhm, prompt-cache, prefill, web-fetch).

Agent loops re-pay the same prefill over and over. withOhm sits on the wire:
identical calls replay from Redis instead of re-billing your provider. You keep
BYOK model billing; Ohm rents the plumbing.

Attach once via local stdio MCP (pip install withohm-mcp):
• ohm_chat — OpenAI-compatible chat through Ohm’s pipe (exact-match Redis replay)
• ohm_fetch_web — purpose-bound public URL → markdown/JSON for agents (robots-aware)
• ohm_savings — dual ledger: estimated provider $ avoided vs Ohm pipe rent + ROI ratio
• ohm_usage — hit ratio, fetches, meters

Why Cursor teams care:
• Fewer duplicate upstream charges on mechanical agent traffic (retries, loops, CI prompts)
• Compliant browse without DIY scrapers
• Public savings receipts / README badges (estimate_only — honest, not a guarantee)

Getting started
1. Intermediate seat: https://www.withohm.dev/subscriptions ($0 membership + meters)
2. Success screen → Add withOhm to Cursor — or https://www.withohm.dev/i
3. Design partners (90-day complimentary): https://www.withohm.dev/design-partners

For Cursor Marketplace / partnerships reviewers
• Gem position: https://github.com/iwasinnam2/ohm/blob/master/docs/GEM_POSITION.md
• BD brief: https://github.com/iwasinnam2/ohm/blob/master/docs/distribution/CURSOR_BD_BRIEF.md
• Ask: approve this listing + optional design-partner intro (partners@withohm.dev)
• Cursor keeps model billing; Ohm rents cache + compliant browse only

Docs: https://www.withohm.dev/docs/cursor
Privacy: https://www.withohm.dev/docs/privacy
API: https://api.withohm.dev/v1
Support: partners@withohm.dev
License: MIT (open-source plugin + gateway); hosted pipe is metered.
```

## Keywords

`ohm`, `withohm`, `withOhm`, `mcp`, `prompt-cache`, `prefill`, `agent-cost`, `web-fetch`, `web-scrape`, `byok`, `openai-compatible`, `agent-browse`, `url-context`, `compliant-fetch-for-agents`, `savings`

## Publish / refresh (employee review path)

1. https://cursor.com/marketplace/publish — paste short + long description above;
   logo `https://www.withohm.dev/ohm-icon-360.png`
2. In the publisher notes / review message field (if present), paste:

```text
Refresh for Cursor employee review: withOhm cuts repeat agent prefill waste via
billing-grade exact-match Redis replay + compliant web fetch. BYOK — we do not
replace Cursor model billing. Plan + BD brief linked in the long description
(GEM_POSITION.md, CURSOR_BD_BRIEF.md). Contact partners@withohm.dev for a
design-partner pilot intro.
```

3. Email follow-up (same day as submit): `marketplace@cursor.com` with subject
   `withOhm marketplace refresh — employee review / gem position` and body
   pointing at the two GitHub docs + this listing.
4. cursor.directory — [CURSOR_DIRECTORY.md](CURSOR_DIRECTORY.md)
5. One-liner everywhere: `Add withOhm MCP from https://www.withohm.dev/i`

## Logo

Prefer `https://www.withohm.dev/ohm-icon-360.png` (or in-repo `assets/logo.svg`)

## Homepage / repo

- https://www.withohm.dev
- https://github.com/iwasinnam2/ohm

## Screenshots to capture (do before submit refresh)

1. Cursor MCP panel with `ohm` tools listed
2. Agent calling `ohm_fetch_web` on a public docs URL
3. `ohm_savings` showing provider avoided + pipe rent + ROI ratio
4. withohm.dev billing success “Add to Cursor” button
5. Optional: public savings receipt page (`/r/{token}`)

Store under `docs/listings/screenshots/` when ready (git-lfs or compressed PNG).

## Config defaults (plugin)

`OHM_BASE_URL` default: `https://api.withohm.dev/v1`  
Required: `OHM_API_KEY`  
Optional: `OHM_UPSTREAM_KEY`

Remote URL MCP is **not** shipped — local stdio only.
