# Integrations

withOhm connects to the tools you already trust. The brand board below is the
map — official homes for each product, plus a **Set up** link into withOhm.

Interactive configs (paste your key, copy JSON / one-click Cursor) live on
[/connections](/connections).

## Before any host

1. Get a key: the [$0 Intermediate seat](/billing/intermediate) issues an `sk-at-…` key at checkout.
2. Install the MCP server once: `pip install withohm-mcp`.
3. Or skip MCP and point any OpenAI SDK at `https://api.withohm.dev/v1` — see [Quickstart](/docs/quickstart).

Env for MCP hosts: `OHM_API_KEY` (required), optional `OHM_UPSTREAM_KEY` (BYOK on misses), optional `OHM_BASE_URL` (default `https://api.withohm.dev/v1`).

## Host setups

Deep-dive configs for each coding agent are on [/connections](/connections).
Shortcut: [Cursor / MCP](/docs/cursor).

### JetBrains (AI Assistant)

Install the thin withOhm plugin (Marketplace or Install Plugin from Disk), then open
**Settings → Tools → withOhm**, paste your `sk-at-…` key, and Apply. The plugin
registers stdio `ohm-mcp` for AI Assistant (IDE 2025.1+). You still need
`pip install withohm-mcp` on PATH. Source and build:
[`ide-plugins/jetbrains/`](https://github.com/iwasinnam2/ohm/tree/master/ide-plugins/jetbrains).
