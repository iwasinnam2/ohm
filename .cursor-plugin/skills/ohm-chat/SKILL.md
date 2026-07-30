---
name: ohm-chat
description: >
  Chat through withOhm via MCP ohm_chat (OpenAI-compatible ingress + Redis prompt
  replay). Use when the user wants prompt cache, BYOK model calls through Ohm,
  or chat with optional compliant fetch_urls — withOhm, ohm, prompt-cache, BYOK.
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
