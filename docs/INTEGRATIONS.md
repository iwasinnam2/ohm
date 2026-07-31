# Integrations

withOhm connects to your tools; it does not ask your tools to come to it. Every host below speaks MCP (Model Context Protocol), and every host gets the same seven tools from one small stdio server.

Live version with pre-filled configs: [withohm.dev/connections](https://www.withohm.dev/connections). Site doc counterpart: `site/content/docs/integrations.md`.

## Before any host

1. Get a key: the $0 Intermediate seat at [withohm.dev/billing/intermediate](https://www.withohm.dev/billing/intermediate) issues an `sk-at-…` key at checkout.
2. Install the server once: `pip install withohm-mcp` (monorepo dev: `pip install -e ".[mcp]"`).

Every config is the same idea: run `ohm-mcp`, hand it `OHM_API_KEY`. Optional: `OHM_UPSTREAM_KEY` (BYOK provider key for cache misses), `OHM_BASE_URL` (defaults to `https://api.withohm.dev/v1`).

## Cursor

Preferred: one-click deeplink from `/connections` or `/i`. Manual — `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

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

```bash
claude mcp add ohm --env OHM_API_KEY=sk-at-… -- ohm-mcp
```

## VS Code (Copilot agent mode)

`.vscode/mcp.json`:

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

`~/.codeium/windsurf/mcp_config.json`:

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

`settings.json`:

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

## Verify

Ask the agent to call `ohm_usage` — a JSON usage snapshot means the pipe is live.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Host can't start the server | `ohm-mcp` not on PATH | Install into the Python the host uses, or use `"command": "python", "args": ["-m", "ohm_mcp"]` |
| `OHM_API_KEY is required` | Key missing from env block | Paste the `sk-at-…` key into the config |
| 401 / 403 | Wrong or revoked key | Re-issue from billing |
| Real models error, `mock` works | No BYOK key on cache misses | Set `OHM_UPSTREAM_KEY` or pass `upstream_api_key` to `ohm_chat` |
| Fetch refused | Purpose not allowed | Call `ohm_policy` for permitted purposes |

## Roadmap

- **Hosted remote MCP** — one URL attach over streamable HTTP, no local install.
- **Slack app** — usage alerts and fetch summaries in channels.
- **Automation platforms** — Zapier / Make connectors.
