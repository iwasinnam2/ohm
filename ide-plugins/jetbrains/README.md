# withOhm — JetBrains AI Assistant plugin

Thin IntelliJ Platform plugin that registers the withOhm MCP stdio server
(`ohm-mcp`) for **JetBrains AI Assistant** (2025.1+). It does **not** bundle
the gateway, Rust edge, or Python MCP sources — install `withohm-mcp` from PyPI
separately.

## Prerequisites

- JDK 21 (build) / any JetBrains IDE 2025.1+ (runtime)
- [AI Assistant](https://plugins.jetbrains.com/plugin/22282-ai-assistant) enabled
- `pip install withohm-mcp` so `ohm-mcp` is on `PATH`
- Tenant key (`sk-at-…`) from [withohm.dev/billing/intermediate](https://www.withohm.dev/billing/intermediate)

## Build (Marketplace zip)

```bash
cd ide-plugins/jetbrains
./gradlew buildPlugin
# → build/distributions/withohm-jetbrains-0.1.0.zip
```

The zip is what you upload to [JetBrains Marketplace](https://plugins.jetbrains.com/docs/marketplace/uploading-a-new-plugin.html)
(or install locally via **Settings → Plugins → ⚙️ → Install Plugin from Disk…**).

## Local smoke

1. Install the zip from Disk; restart the IDE.
2. Open **Settings → Tools → withOhm**.
3. Enable the checkbox, paste `OHM_API_KEY`, optional BYOK + base URL.
4. Click **Apply to AI Assistant** (or Apply in the settings dialog).
5. Confirm `ohm` appears under **Settings → Tools → AI Assistant → Model Context Protocol**.
6. In AI chat, ask for usage / models — tools `ohm_usage`, `ohm_models`, etc. should run.

If auto-write fails, use **Copy MCP JSON** and paste into the AI Assistant MCP dialog.

## What it writes

Merges (does not wipe other servers) into AI Assistant `mcp.json`:

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

Typical paths:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/JetBrains/AIAssistant/mcp.json` |
| Windows | `%APPDATA%\JetBrains\AIAssistant\mcp.json` |
| Linux | `~/.config/JetBrains/AIAssistant/mcp.json` |

Secrets stay in the IDE **PasswordSafe**; the file is updated on Apply / project open when enabled.

## Marketplace upload

1. Create a Vendor profile on [plugins.jetbrains.com](https://plugins.jetbrains.com).
2. Upload `build/distributions/withohm-jetbrains-0.1.0.zip`.
3. Use the draft text in [`docs/listings/JETBRAINS_MARKETPLACE.md`](../../docs/listings/JETBRAINS_MARKETPLACE.md).

## Non-goals (v1)

- Reimplementing the eight MCP tools in Kotlin
- Bundling Python / gateway / site
- Remote HTTP MCP as default
- IDEs before 2025.1
