---
name: ohm-fetch-web
description: >
  Compliant public URL scrape via withOhm MCP ohm_fetch_web (markdown or JSON).
  Use when the user or agent needs page content from public URLs, web context for
  coding agents, docs scrape, catalog pages, or browse-without-browser — withOhm,
  ohm, web-fetch, web-scrape, URL context.
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

Requires Ohm MCP attached (`OHM_BASE_URL`, `OHM_API_KEY`). Terms/DPA bound at Checkout. See `docs/CURSOR.md`.

Share line: `Add withOhm MCP from https://www.withohm.dev/i`
