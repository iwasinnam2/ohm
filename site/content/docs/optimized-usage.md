# Optimized usage

How to run withOhm at the standard it was built for. Short version: let the cache do the repetitive work, fetch with intent, and read your own meters.

Prerequisites: a connected host ([Integrations](/docs/integrations)) and the [command catalog](/docs/commands) for parameter detail.

## 1. Cache-first prompting

The pipe replays identical prompts from Redis instead of re-billing the provider. To benefit:

- **Keep repeated prompts byte-identical.** Templates, lint explanations, doc lookups — same wording, same model, same replay.
- **Don't inject noise.** Timestamps, request ids, or "please" variations in otherwise-identical prompts turn cache hits into misses.
- **Check it's working.** `ohm_savings` shows replayed prompts and spend avoided; `ohm_usage` shows the hit ratio. A low ratio usually means your prompts vary when they don't need to.

## 2. Fetch with intent

Two ways to bring the public web into context — pick deliberately:

- **`ohm_fetch_web`** when the page content is the deliverable: scraping docs, reading a changelog, comparing listings. `format="json"` gives structured title/text/meta/JSON-LD; `query` focuses the summary.
- **`ohm_chat` with `fetch_urls`** when you want the model to reason over pages in one round trip: "read these three pages and answer X."

Rules of the road: public pages only, and every fetch declares a purpose. If a fetch is refused, `ohm_policy` tells you which purposes your seat allows — don't guess.

## 3. BYOK, set once

BYOK ("bring your own keys") means your provider key — OpenAI, Anthropic — rides each request in the `X-Ohm-Upstream-Key` header and is not stored. Set `OHM_UPSTREAM_KEY` once in your host config and forget it; only reach for `ohm_chat`'s `upstream_api_key` param when a single call needs a different key. The `mock` model needs no key at all — use it to smoke-test a new connection.

## 4. Read your own meters

Once a week (or when a bill surprises you):

1. `ohm_usage` — hit ratio, fetch counts, estimated pipe rent.
2. `ohm_savings` — what the cache avoided.
3. `ohm_providers` — upstream health, if calls have been flaky.

You pay pipe rent (routing, caching, compliant fetch), not token wholesale — so the lever you control is the hit ratio and the fetch count, and both are visible on demand.

## 5. Troubleshoot in order

1. `ohm_usage` returns? The pipe and your key are fine.
2. `mock` works but gpt/claude fails? BYOK key missing or wrong — see step 3 above.
3. Fetch refused? `ohm_policy` for the allowed purposes.
4. Still stuck? `ohm_providers` for upstream/failover status, then [Status](/status).

## The loop, in one sitting

```text
1. ohm_models                      → pick a model
2. ohm_chat(prompt, model)         → work; identical reruns replay free
3. ohm_fetch_web(urls, purpose)    → context when the web is needed
4. ohm_savings / ohm_usage         → confirm the pipe is paying for itself
```
