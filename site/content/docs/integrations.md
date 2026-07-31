# Integrations

withOhm connects to your tools; it does not ask your tools to come to it. Every host below speaks MCP (Model Context Protocol — an open standard that lets coding agents call external services), and every host gets the same seven tools from one small server.

The interactive version of this page, with configs pre-filled from your key, is at [/connections](/connections).

## Before any host

1. Get a key: the [$0 Intermediate seat](/billing/intermediate) issues an `sk-at-…` key at checkout.
2. Install the server once: `pip install withohm-mcp`.

Every config below is the same idea: run `ohm-mcp`, hand it `OHM_API_KEY`. Optional extras: `OHM_UPSTREAM_KEY` (your own provider key — BYOK, "bring your own keys" — used on cache misses) and `OHM_BASE_URL` (defaults to `https://api.withohm.dev/v1`).

## Cursor

Preferred: one-click. Paste your key at [/connections](/connections) or [/i](/i) and click **Add withOhm to Cursor** — the deeplink opens Cursor's MCP install confirm with the config pre-filled.

Manual: add to `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (this project):

```json
{
  "mcpServers": {
    "ohm": {
      "command": "ohm-mcp",
      "env": { "OHM_API_KEY": "sk-at-…" }
    }
  }
}
```

## Claude Code

One terminal command:

```bash
claude mcp add ohm --env OHM_API_KEY=sk-at-… -- ohm-mcp
```

## VS Code (Copilot agent mode)

Add `.vscode/mcp.json` to your workspace:

```json
{
  "servers": {
    "ohm": {
      "type": "stdio",
      "command": "ohm-mcp",
      "env": { "OHM_API_KEY": "sk-at-…" }
    }
  }
}
```

## Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "ohm": {
      "command": "ohm-mcp",
      "env": { "OHM_API_KEY": "sk-at-…" }
    }
  }
}
```

## Zed

Add to `settings.json` (`zed: open settings`):

```json
{
  "context_servers": {
    "ohm": {
      "source": "custom",
      "command": "ohm-mcp",
      "args": [],
      "env": { "OHM_API_KEY": "sk-at-…" }
    }
  }
}
```

## Verify the connection

In any host, ask the agent to call `ohm_usage`. A JSON usage snapshot back means the pipe is live. Then try:

```text
ohm_fetch_web(urls=["https://example.com"], purpose="public_web_retrieval")
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Host can't start the server | `ohm-mcp` not on PATH | `pip install withohm-mcp` in the Python the host uses, or use `"command": "python", "args": ["-m", "ohm_mcp"]` |
| `OHM_API_KEY is required` | Key missing from env block | Paste your `sk-at-…` key into the config |
| 401 / 403 responses | Wrong or revoked key | Re-issue from [/billing/intermediate](/billing/intermediate) |
| Real models error, `mock` works | No BYOK key on cache misses | Set `OHM_UPSTREAM_KEY`, or pass `upstream_api_key` to `ohm_chat` |
| Fetch refused | Purpose not allowed for the URL | Call `ohm_policy` to see permitted purposes and limits |

## Coming to the grid

- **Hosted remote MCP** — one URL attach over streamable HTTP, no local install.
- **Slack app** — usage alerts and fetch summaries where your team talks.
- **Automation platforms** — Zapier / Make connectors for no-code pipelines.

See the [command catalog](/docs/commands) for what each tool does, and [optimized usage](/docs/optimized-usage) for getting the most from the pipe.
