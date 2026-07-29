# Quickstart

Change one base URL (or one Cursor attach). Keep your keys and SDKs.

## Paths

1. **Self-serve:** [/billing](/billing) — Checkout issues your withOhm key once.
2. **Subscriptions:** [/subscriptions](/subscriptions) — Free trial, Intermediate, and Enterprise (design-partner rank).
3. Point SDKs at `http://localhost:8081/v1` (or `https://api.withohm.dev/v1` after cutover).
4. BYOK: send your provider key as `X-Ohm-Upstream-Key`. Authorization stays `sk-at-…`.
5. Optional: [Add withOhm to Cursor](/docs/cursor).

## Python

```python
from at_utility_sdk import openai_client, LOCAL_BASE_URL

client = openai_client(
    "sk-at-dev",
    base_url=LOCAL_BASE_URL,
    upstream_api_key="sk-proj-...",
)
```

Identical second call → Redis cache hit (`x-at-cache: HIT`).

## curl

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```
