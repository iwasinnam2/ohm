# Command catalog

The complete withOhm surface in any connected host: seven MCP tools, each mirrored by a slash skill in Cursor (`/ohm-chat`, `/ohm-fetch-web`, and so on). Connect a host first — see [Integrations](/docs/integrations) or [/connections](/connections).

| Tool | When to reach for it |
|------|----------------------|
| `ohm_chat` | Route a model call through the pipe so identical prompts replay from cache |
| `ohm_fetch_web` | Pull public web pages into context, compliantly |
| `ohm_usage` | Check your meters: cache hits, fetches, pipe rent |
| `ohm_savings` | See what the cache has saved you |
| `ohm_models` | List the model ids the pipe routes to |
| `ohm_providers` | Check upstream provider and failover health |
| `ohm_policy` | See which web-fetch purposes are allowed |

## ohm_chat

Chat through the pipe (OpenAI-compatible). Identical prompts replay from the Redis cache instead of hitting the provider again.

| Param | Default | Notes |
|-------|---------|-------|
| `prompt` | (required) | User message |
| `model` | `mock` | `mock` works without keys; gpt/claude need BYOK |
| `fetch_urls` | none | Optional public URLs attached as compliant web context |
| `purpose` | `public_web_retrieval` | Applies when `fetch_urls` is set |
| `upstream_api_key` | `""` | Per-call BYOK override (else `OHM_UPSTREAM_KEY`) |

Example prompt to your agent:

```text
Use ohm_chat to summarize https://example.com/changelog with model mock.
```

## ohm_fetch_web

Compliant public-web fetch: robots-gated, PII-redacted, metered as `ohm_web_fetch`. Public pages only.

| Param | Default | Notes |
|-------|---------|-------|
| `urls` | (required) | Public `http(s)` pages |
| `purpose` | `public_web_retrieval` | Also: `business_catalog`, `public_company_info`, `job_listings` |
| `query` | `""` | Optional focus question for the summarizer |
| `format` | `markdown` | `markdown` or `json` (title, text, meta, JSON-LD) |

Example:

```text
Use ohm_fetch_web on these three docs pages, format json, query "auth setup".
```

## ohm_usage

No params. Returns cache hit ratio, fetch counts, and estimated pipe rent from `GET /v1/usage`.

```text
Call ohm_usage and tell me my cache hit ratio this cycle.
```

## ohm_savings

No params. Returns replayed prompt counts and estimated spend avoided from `GET /v1/savings`. Pair with `ohm_usage` for the full meter picture.

```text
Call ohm_savings — how much has the cache saved me?
```

## ohm_models

No params. Lists the model ids the pipe routes to from `GET /v1/models`, including BYOK upstreams. Use it before picking a `model` for `ohm_chat`.

```text
Call ohm_models and pick the cheapest model that can handle this task.
```

## ohm_providers

No params. Returns upstream provider and failover status from `GET /v1/providers`. Check this first when a real (non-mock) model call errors.

```text
ohm_chat is failing on gpt — call ohm_providers and check upstream health.
```

## ohm_policy

No params. Returns the allowed web-fetch purposes and their limits from `GET /v1/compliance/policy`. Use it to pick the right `purpose`, or to explain a refused fetch.

```text
Call ohm_policy — is job_listings an allowed purpose on my seat?
```

## ohm_receipt (and demo mint)

Mint a public savings receipt (`POST /v1/savings/receipt`). The [/demo](/demo)
**Mint public receipt** button after miss→HIT is the same mint — no MCP required.
Receipts are `estimate_only` (display name + aggregates; never prompts).

## Path + hit ratio

Send `X-Ohm-Path` (or JSON `ohm_path`) on chat to label a frequency farm. Read
inventory with `GET /v1/ledger/hit-ratio` (tenant) or
`GET /v1/org/ledger/hit-ratio?month=YYYY-MM&group_by=path|cost_center` (org).

## Environment

| Var | Role |
|-----|------|
| `OHM_API_KEY` | Tenant key (`sk-at-…`) — required |
| `OHM_BASE_URL` | Defaults to `https://api.withohm.dev/v1` |
| `OHM_UPSTREAM_KEY` | Optional BYOK provider key for cache misses |

Next: [optimized usage](/docs/optimized-usage) — the workflow that gets the most out of these seven.
