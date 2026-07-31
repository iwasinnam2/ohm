# Add Ohm to Cursor

After Checkout, success is one job: **Add Ohm to Cursor** — a deeplink into Cursor’s MCP install confirm with your seat already wired. Manual JSON is a fallback only.

## One-click

1. Pay on [withohm.dev/billing](https://www.withohm.dev/billing) (or local `/billing`)
2. Optional: paste provider key on the success screen (BYOK)
3. Click **Add Ohm to Cursor** → confirm in Cursor

```text
cursor://anysphere.cursor-deeplink/mcp/install?name=ohm&config=<base64>
```

## Manual fallback

```json
{
  "mcpServers": {
    "ohm": {
      "command": "python",
      "args": ["-m", "ohm_mcp"],
      "env": {
        "OHM_BASE_URL": "https://api.withohm.dev/v1",
        "OHM_API_KEY": "sk-at-YOUR_ISSUED_KEY",
        "OHM_UPSTREAM_KEY": ""
      }
    }
  }
}
```

Install once (slim client — no gateway stack):

```powershell
pip install withohm-mcp
# monorepo dev alternative: pip install -e ".[mcp]"
```

`OHM_API_KEY` is required (Checkout at https://www.withohm.dev/billing/intermediate). Terms/DPA are bound at seat mint — MCP does not forge per-request legal acks. See [`.cursor/mcp.json.example`](../.cursor/mcp.json.example) for local-only smoke.

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

Other hosts (Claude Code, VS Code, Windsurf, Zed): see [INTEGRATIONS.md](INTEGRATIONS.md).

### `ohm_fetch_web`

| Param | Default | Notes |
|-------|---------|-------|
| `urls` | (required) | Public `http(s)` pages |
| `purpose` | `public_web_retrieval` | Also: `business_catalog`, `public_company_info`, `job_listings` |
| `query` | `""` | Optional focus question |
| `format` | `markdown` | `markdown` or `json` (title, text, meta, JSON-LD) |

Metered as `ohm_web_fetch`. Public pages only — see [LEGAL.md](LEGAL.md).

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

Slash skills (project): `/ohm-fetch-web`, `/ohm-usage`, `/ohm-chat` under [`.cursor/skills/`](../.cursor/skills/).
