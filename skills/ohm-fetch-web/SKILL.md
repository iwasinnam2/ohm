---
name: ohm-fetch-web
description: Compliant Ohm URL scrape via MCP ohm_fetch_web (markdown or JSON).
disable-model-invocation: true
---

# Ohm fetch web

Call the Ohm MCP tool `ohm_fetch_web` for compliant public-page retrieval.

## When to use

- Need page content without hand-browsing
- Prefer structured scrape → set `format` to `json`
- Default prose excerpts → `format` `markdown`

## Call

```text
ohm_fetch_web(
  urls=["https://example.com"],
  purpose="public_web_retrieval",
  query="",
  format="markdown"   # or "json"
)
```

**Purposes:** `public_web_retrieval`, `business_catalog`, `public_company_info`, `job_listings`.

**JSON shape:** `url`, `title`, `text`, optional `meta`, `json_ld`.

Requires Ohm MCP attached (`OHM_BASE_URL`, `OHM_API_KEY`). See `docs/CURSOR.md`.
