# Optimized usage

How to run withOhm at the standard it was built for. Short version: let the cache do the repetitive work, fetch with intent, and read your own meters. Site counterpart: `site/content/docs/optimized-usage.md`.

## 1. Cache-first prompting

The pipe replays identical prompts from Redis instead of re-billing the provider.

- Keep repeated prompts byte-identical — templates, lint explanations, doc lookups.
- Don't inject noise (timestamps, request ids) into otherwise-identical prompts.
- Verify with `ohm_savings` (spend avoided) and `ohm_usage` (hit ratio).

## 2. Fetch with intent

- `ohm_fetch_web` when page content is the deliverable; `format="json"` for structured output, `query` to focus the summary.
- `ohm_chat` with `fetch_urls` when the model should reason over pages in one round trip.
- Public pages only, every fetch declares a purpose. Refused? `ohm_policy` lists what your seat allows.

## 3. BYOK, set once

Provider keys ride the `X-Ohm-Upstream-Key` header per request and are not stored. Set `OHM_UPSTREAM_KEY` in the host config; use `ohm_chat`'s `upstream_api_key` param only for one-off overrides. `mock` needs no key — use it to smoke-test connections.

## 4. Read your own meters

`ohm_usage` → hit ratio, fetches, pipe rent. `ohm_savings` → what the cache avoided. `ohm_providers` → upstream health. The levers you control are hit ratio and fetch count; both are visible on demand.

## 5. Troubleshoot in order

1. `ohm_usage` returns → pipe and key fine.
2. `mock` works, gpt/claude fails → BYOK missing.
3. Fetch refused → `ohm_policy`.
4. Still stuck → `ohm_providers`, then status page.

## The loop

```text
1. ohm_models                      → pick a model
2. ohm_chat(prompt, model)         → work; identical reruns replay free
3. ohm_fetch_web(urls, purpose)    → context when the web is needed
4. ohm_savings / ohm_usage         → confirm the pipe is paying for itself
```
