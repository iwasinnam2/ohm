# Quickstart

Change one base URL (or one editor attach). Keep your keys and SDKs.

## Paths

1. **Self-serve:** [/billing/intermediate](/billing/intermediate) — Checkout issues your withOhm key once.
2. **Subscriptions:** [/subscriptions](/subscriptions) — Intermediate ($0 membership + meters) and Enterprise (fixed monthly bundles).
3. Point SDKs at `http://localhost:8081/v1` (or `https://api.withohm.dev/v1` after cutover).
4. BYOK (bring your own keys): send your provider key as `X-Ohm-Upstream-Key`. Authorization stays `sk-at-…`.
5. Optional: connect your editor — [Cursor](/docs/cursor), or [any MCP host](/docs/integrations) (Claude Code, VS Code, Windsurf, Zed).
6. **Enterprise:** [/billing/enterprise](/billing/enterprise) — negotiate transaction usage agreements.

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
