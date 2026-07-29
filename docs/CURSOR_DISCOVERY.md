# Getting withOhm offered in Cursor (contextual install)

## What you are seeing

When someone types a brand or product name in chat, Cursor sometimes shows a transient **install plugin** chip. Staff have described this as detecting **strings in the prompt** and suggesting marketplace plugins — not a publisher-configured trigger list.

There is **no** `triggers` / `suggestWhen` field in `plugin.json`, and **no** public API to register situational install offers.

## What we can control

| Lever | Effect |
|-------|--------|
| Official Marketplace listing (reviewed) | Prerequisite — chips only make sense for listed plugins |
| `name`: `ohm`, `displayName`: `withOhm` | Brand tokens users (and likely matchers) hit |
| Rich `keywords` + first-line `description` | Search + possible string overlap with prompts |
| Ship `skills/` + MCP in the plugin | After install, agent actually uses Ohm for those jobs |
| Checkout deeplink | **You** fully control intentional install |
| cursor.directory + Forum posts | Browse / social discovery |

## What we cannot control

- Exact prompt→plugin matching algorithm
- Guaranteed offer when someone says “scrape this URL” without saying Ohm
- Repo-aware recommendations (deps/env) — requested by community, not a publisher feature yet

## withOhm packaging checklist

1. Stay listed via https://cursor.com/marketplace/publish
2. Keep brand in prompts/docs users copy: **withOhm**, **ohm**, `ohm_fetch_web`
3. Keywords include: `withohm`, `prompt-cache`, `web-fetch`, `byok`, `agent-browse`
4. Plugin `skills/` descriptions include “Use when …” + brand tokens (done in-repo)
5. Primary conversion remains `/billing/success` → `cursor://…/mcp/install`

## Practical growth implication

Treat contextual chips as **bonus discovery** if Cursor’s matcher knows your brand. Treat **deeplink + Marketplace search + GTM fishing** ([LAUNCH_GTM.md](LAUNCH_GTM.md)) as the reliable funnel. Partnership / first-party placement with Cursor is a separate BD track ([BRAND.md](BRAND.md)).
