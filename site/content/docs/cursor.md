# Cursor / MCP (compatibility)

withOhm’s primary product is the OpenAI-compatible pipe and [Agent Shell](/workbench).
MCP in Cursor is an optional compatibility client — not required.

After Checkout, success may offer **Add withOhm to Cursor** — a deeplink into
Cursor’s MCP install confirm. Manual JSON is a fallback.

## One-click (preferred)

1. Finish Stripe Checkout on [/billing/intermediate](/billing/intermediate)
2. On success, optionally paste your provider key (BYOK)
3. Click **Add withOhm to Cursor** → confirm in Cursor’s MCP UI

Deeplink shape (built automatically on success):

```text
cursor://anysphere.cursor-deeplink/mcp/install?name=ohm&config=<base64>
```

## Manual fallback

Only if the deeplink isn’t available:

```json
{
  "mcpServers": {
    "ohm": {
      "command": "python",
      "args": ["-m", "ohm_mcp"],
      "env": {
        "OHM_BASE_URL": "https://api.withohm.dev/v1",
        "OHM_API_KEY": "sk-at-…",
        "OHM_UPSTREAM_KEY": ""
      }
    }
  }
}
```

`pip install -e ".[mcp]"` once from the withOhm repository (or install the published package when available).

## Usable commands (MCP tools)

| Command | Purpose |
|---------|---------|
| `ohm_fetch_web` | Compliant URL fetch → redacted **markdown** or **JSON** context |
| `ohm_usage` | Usage snapshot (`GET /v1/usage`) |
| `ohm_chat` | Chat through Ohm; optional `fetch_urls` for web context |
| `ohm_savings` | Cache savings snapshot (`GET /v1/savings`) |
| `ohm_models` | Routable model ids (`GET /v1/models`) |
| `ohm_providers` | Upstream provider / failover status (`GET /v1/providers`) |
| `ohm_policy` | Allowed web-fetch purposes (`GET /v1/compliance/policy`) |

Full parameters and example prompts for every tool: [command catalog](/docs/commands). Other hosts (Claude Code, VS Code, Windsurf, Zed): [integrations](/docs/integrations).

### `ohm_fetch_web`

| Param | Default | Notes |
|-------|---------|-------|
| `urls` | (required) | Public `http(s)` pages |
| `purpose` | `public_web_retrieval` | Also: `business_catalog`, `public_company_info`, `job_listings` |
| `query` | `""` | Optional focus question |
| `format` | `markdown` | `markdown` or `json` (title, text, meta, JSON-LD) |

Metered as `ohm_web_fetch`. Public pages only.

### `ohm_usage`

No params. Returns cache hit ratio, fetches, and web attach rate.

### `ohm_chat`

| Param | Default | Notes |
|-------|---------|-------|
| `prompt` | (required) | User message |
| `model` | `mock` | gpt/claude need BYOK |
| `fetch_urls` | none | Optional compliant web attach |
| `purpose` | `public_web_retrieval` | When `fetch_urls` is set |
| `upstream_api_key` | `""` | Overrides `OHM_UPSTREAM_KEY` |

### Env

| Var | Role |
|-----|------|
| `OHM_BASE_URL` | Edge `/v1` (default `https://api.withohm.dev/v1`; local smoke `http://127.0.0.1:8081/v1`) |
| `OHM_API_KEY` | Tenant key (`sk-at-…`) |
| `OHM_UPSTREAM_KEY` | Optional BYOK for cache misses |

## OpenAI-compatible base URL

| Field | Value |
|-------|--------|
| base URL | `https://api.withohm.dev/v1` |
| API key | withOhm `sk-at-…` |
| Upstream | Header `X-Ohm-Upstream-Key` |
