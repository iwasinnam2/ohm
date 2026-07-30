---
name: ohm-usage
description: >
  withOhm usage snapshot via MCP ohm_usage (cache hits, fetches, web attach).
  Use when checking meter spend, hit ratio, or fetch caps — withOhm, ohm, usage.
---

# Ohm usage

Call the Ohm MCP tool `ohm_usage` for a usage snapshot.

## Call

```text
ohm_usage()
```

Returns cache hit ratio, fetch counts, and web attach rate from `GET /v1/usage`.

Requires Ohm MCP attached (`OHM_BASE_URL`, `OHM_API_KEY`). See `docs/CURSOR.md`.
