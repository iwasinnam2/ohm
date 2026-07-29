# Add Ohm to Cursor

After Checkout, the success screen’s primary action is **Add Ohm to Cursor** — a one-click deeplink into Cursor’s MCP install confirm. Your Ohm key is already in the config. That is the product path; manual JSON is only a fallback.

## One-click (preferred)

1. Finish Stripe Checkout on [/billing](/billing)
2. On success, optionally paste your provider key (BYOK)
3. Click **Add Ohm to Cursor** → confirm in Cursor’s MCP UI

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
        "OHM_BASE_URL": "http://127.0.0.1:8081/v1",
        "OHM_API_KEY": "sk-at-…",
        "OHM_UPSTREAM_KEY": ""
      }
    }
  }
}
```

`pip install -e ".[mcp]"` once from the Ohm repo (or install the published package when available). Tools: `ohm_fetch_web`, `ohm_usage`, `ohm_chat`.

## OpenAI-compatible base URL

| Field | Value |
|-------|--------|
| base URL | `http://127.0.0.1:8081/v1` |
| API key | Ohm `sk-at-…` |
| Upstream | Header `X-Ohm-Upstream-Key` |
