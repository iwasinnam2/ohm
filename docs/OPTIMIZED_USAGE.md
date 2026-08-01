# Optimized usage

How to run withOhm at the standard it was built for. Short version: let the cache do the repetitive work, fetch with intent, and read your own meters. Site counterpart: `site/content/docs/optimized-usage.md`.

Wedge: [GEM_POSITION.md](GEM_POSITION.md).

## 1. Cache-first prompting

The pipe replays **byte-identical** prompts from Redis instead of re-billing the provider.

- Keep repeated prompts identical — templates, lint explanations, doc lookups.
- Don't inject noise (timestamps, request ids, random session salts) into otherwise-identical prompts.
- Verify with `ohm_savings` (provider avoided + pipe rent + ROI) and `ohm_usage` (hit ratio).

## 2. Cursor / agent hit-rate playbook

Agent products inflate context every turn. Exact-match still wins when the
*mechanical* parts of traffic repeat. Raise hit ratio with discipline:

| Do | Don't |
|----|--------|
| Stable system prompt / tool preamble across a session | Embed `Date.now()`, UUIDs, or “run id” in cacheable cores |
| Cacheable core = model + messages that retry on tool failure | Mix volatile tool noise into the same message blob you want replayed |
| Separate one-off explore chats from CI / loop prompts | Expect human chat (always-new text) to hit |
| Use `cache_control: "no_store"` when you need fresh sampling | Assume temperature>0 diversity on a HIT (HIT is intentional replay) |
| Re-run the same lint/doc/test prompt suite through Ohm | Change whitespace/CRLF only — normalization helps, semantic drift does not |

**Prefill waste pattern:** agent retries the same completion after a tool error →
second call should be a HIT. If it is always a MISS, something in the payload
is mutating (clock, ids, reordered tools).

**Compaction:** host “context summarised” reduces window bloat; Ohm replay
removes *duplicate full-price journeys* when the compacted (or raw) prompt
repeats. They stack; neither replaces the other.

## 3. Fetch with intent

- `ohm_fetch_web` when page content is the deliverable; `format="json"` for structured output, `query` to focus the summary.
- `ohm_chat` with `fetch_urls` when the model should reason over pages in one round trip.
- Public pages only, every fetch declares a purpose. Refused? `ohm_policy` lists what your seat allows.

## 4. BYOK, set once

Provider keys ride the `X-Ohm-Upstream-Key` header per request and are not stored. Set `OHM_UPSTREAM_KEY` in the host config; use `ohm_chat`'s `upstream_api_key` param only for one-off overrides. `mock` needs no key — use it to smoke-test connections.

## 5. Read your own meters (dual ledger)

`ohm_usage` → hit ratio, fetches, pipe rent.  
`ohm_savings` → **estimated provider $ avoided**, **pipe rent**, **roi_ratio** (provider÷pipe).  
`ohm_providers` → upstream readiness.

All savings figures are `estimate_only` (blended list rate × hit tokens). Not a guarantee.

## 6. Troubleshoot in order

1. `ohm_usage` returns → pipe and key fine.
2. `mock` works, gpt/claude fails → BYOK missing.
3. Fetch refused → `ohm_policy`.
4. Still stuck → `ohm_providers`, then status page.

## The loop

```text
1. ohm_models                      → pick a model
2. ohm_chat(prompt, model)         → work; identical reruns replay
3. ohm_fetch_web(urls, purpose)    → context when the web is needed
4. ohm_savings / ohm_usage         → confirm ROI (provider avoided ÷ pipe rent)
5. ohm_receipt                     → mint a public badge when the number is real
```
