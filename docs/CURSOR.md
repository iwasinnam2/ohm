# Add Ohm to Cursor

After Checkout, success is one job: **Add Ohm to Cursor** — a deeplink into Cursor’s MCP install confirm with your seat already wired. Manual JSON is a fallback only.

## One-click

1. Pay on [withohm.dev/billing](https://withohm.dev/billing) (or local `/billing`)
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
        "OHM_BASE_URL": "http://127.0.0.1:8081/v1",
        "OHM_API_KEY": "sk-at-dev",
        "OHM_UPSTREAM_KEY": ""
      }
    }
  }
}
```

`pip install -e ".[mcp]"` once from the repo. Tools: `ohm_fetch_web`, `ohm_usage`, `ohm_chat`. See also [`.cursor/mcp.json.example`](../.cursor/mcp.json.example).
