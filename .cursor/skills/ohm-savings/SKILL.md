---
name: ohm-savings
description: >
  withOhm cache savings snapshot via MCP ohm_savings (replayed prompts,
  estimated spend avoided). Use when checking how much the prompt cache is
  saving — withOhm, ohm, savings, cache.
---

# Ohm savings

Call the Ohm MCP tool `ohm_savings` for a cache savings snapshot.

## Call

```text
ohm_savings()
```

Returns replayed prompt counts and estimated spend avoided from
`GET /v1/savings`. Pair with `/ohm-usage` for the full meter picture.

Requires Ohm MCP attached (`OHM_BASE_URL`, `OHM_API_KEY`). See `docs/CURSOR.md`.
