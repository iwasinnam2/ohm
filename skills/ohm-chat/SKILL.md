---
name: ohm-chat
description: Chat through Ohm via MCP ohm_chat; optional compliant fetch_urls.
disable-model-invocation: true
---

# Ohm chat

Call the Ohm MCP tool `ohm_chat` for OpenAI-compatible chat through Ohm (Redis cache on identical prompts).

## Call

```text
ohm_chat(
  prompt="…",
  model="mock",
  fetch_urls=None,              # or ["https://example.com"]
  purpose="public_web_retrieval",
  upstream_api_key=""           # BYOK override; else OHM_UPSTREAM_KEY
)
```

For gpt/claude models, set `OHM_UPSTREAM_KEY` or pass `upstream_api_key`.

For scrape-only (no chat), prefer `/ohm-fetch-web`. See `docs/CURSOR.md`.
