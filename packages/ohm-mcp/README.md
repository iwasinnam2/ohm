# ohm-mcp

Slim stdio MCP server for [withOhm](https://www.withohm.dev): prompt cache
replay, dynamic model switching (BYOK), and compliant public-web fetch as
Cursor tools — without installing the full gateway stack.

## Install

```bash
pip install ohm-mcp
```

## Cursor attach

```json
{
  "mcpServers": {
    "ohm": {
      "command": "ohm-mcp",
      "env": {
        "OHM_API_KEY": "sk-at-YOUR_ISSUED_KEY",
        "OHM_UPSTREAM_KEY": "sk-proj-optional-byok-key"
      }
    }
  }
}
```

Get a key from the $0 Intermediate seat at
[withohm.dev/billing/intermediate](https://www.withohm.dev/billing/intermediate).

## Tools

- `ohm_chat` — chat through the pipe; identical prompts replay from Redis cache.
- `ohm_fetch_web` — compliant public URL fetch (robots-gated, PII-redacted, metered).
- `ohm_usage` — usage snapshot: cache hit ratio, fetches, estimated pipe rent.

## Env

| Variable | Required | Purpose |
|---|---|---|
| `OHM_API_KEY` | yes | Your withOhm tenant key (`sk-at-…`) |
| `OHM_BASE_URL` | no | Defaults to `https://api.withohm.dev/v1` |
| `OHM_UPSTREAM_KEY` | no | BYOK provider key for cache-miss model calls |

MIT licensed. The hosted service is commercial — see
[Terms](https://www.withohm.dev/docs/terms).

Note for maintainers: `src/ohm_mcp/__init__.py` in the monorepo root is the
source of truth; run `scripts/sync_ohm_mcp.ps1` before building this package.
