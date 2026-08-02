# Cursor / MCP

Add withOhm to Cursor over MCP — one-click after Checkout, or paste `mcp.json`.
Prefer the [integrations board](/docs/integrations) when you want every host in
one place.

## One-click (preferred)

1. Finish Stripe Checkout on [/billing/intermediate](/billing/intermediate)
2. On success, optionally paste your provider key (BYOK)
3. Click **Add withOhm to Cursor** → confirm in Cursor’s MCP UI

Deeplink shape (built automatically on success):

```text
cursor://anysphere.cursor-deeplink/mcp/install?name=ohm&config=<base64>
```

Also available from [/i](/i) and [/connections](/connections) once you paste a key.

## Manual fallback

Only if the deeplink isn’t available:

```json
{
  "mcpServers": {
    "ohm": {
      "command": "ohm-mcp",
      "env": {
        "OHM_API_KEY": "sk-at-…",
        "OHM_BASE_URL": "https://api.withohm.dev/v1"
      }
    }
  }
}
```

Install the server first: `pip install withohm-mcp`.

## Tools

| Tool | Role |
|------|------|
| `ohm_chat` | Chat through Ohm; optional `fetch_urls` for web context |
| `ohm_fetch_web` | Compliant public-web markdown |
| `ohm_usage` / `ohm_savings` | Meters and dual savings |
| `ohm_models` / `ohm_providers` | Routing status |
| `ohm_policy` | Compliance purposes |
| `ohm_receipt` | Mint a public savings receipt |

Full catalog: [Command catalog](/docs/commands).
