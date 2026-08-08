# JetBrains Marketplace listing draft

Paste / adapt into https://plugins.jetbrains.com (Upload plugin).

**Audience:** JetBrains AI Assistant users on IntelliJ IDEA / PyCharm / WebStorm /
etc. (2025.1+). Same pipe as Cursor MCP — exact-match Redis replay + compliant
web fetch. You rent the plumbing; BYOK keeps model billing with the provider.

Listing counterpart for Cursor: [MARKETPLACE.md](MARKETPLACE.md). Brand:
[docs/BRAND.md](../BRAND.md).

## Name

`withOhm`

## Plugin ID

`dev.withohm.jetbrains`

## Short description (≤160 chars)

```
withOhm: Redis prompt replay + compliant web fetch for JetBrains AI Assistant via ohm-mcp.
```

## Long description

```
withOhm is an AI traffic utility for JetBrains AI Assistant (search: ohm, withOhm,
prompt-cache, MCP, web-fetch).

Agent loops re-pay the same prefill over and over. withOhm sits on the wire:
identical calls replay from Redis instead of re-billing your provider. You keep
BYOK model billing; Ohm rents the plumbing.

This plugin is a thin bridge:
• Settings → Tools → withOhm — store sk-at-… key (PasswordSafe) + optional BYOK
• Registers the ohm stdio MCP server for AI Assistant (same eight tools as Cursor)
• Does not reimplement tools — requires: pip install withohm-mcp

Tools (via ohm-mcp):
• ohm_chat — OpenAI-compatible chat through Ohm’s pipe (exact-match Redis replay)
• ohm_fetch_web — purpose-bound public URL → markdown/JSON (robots-aware)
• ohm_savings / ohm_usage — cache savings + meters
• ohm_receipt — public savings receipt
• ohm_models / ohm_providers / ohm_policy

Get a key: https://www.withohm.dev/billing/intermediate
Docs: https://www.withohm.dev/docs/integrations
```

## Tags

`AI`, `MCP`, `LLM`, `OpenAI`, `Claude`, `cache`, `productivity`

## License

MIT (see repo `LICENSE`)

## Vendor

- Name: Ohm
- Email: partners@withohm.dev
- URL: https://www.withohm.dev

## Source / homepage

- Source: https://github.com/iwasinnam2/ohm (path `ide-plugins/jetbrains/`)
- Homepage: https://www.withohm.dev

## Compatibility

- since-build: `251` (2025.1+)
- Requires AI Assistant plugin for MCP client UI
- Requires local `ohm-mcp` on PATH (`pip install withohm-mcp`)

## Artifact

```bash
cd ide-plugins/jetbrains
./gradlew buildPlugin
# upload: build/distributions/withohm-jetbrains-0.1.0.zip
```

## Install from Disk (pre-Marketplace)

Settings → Plugins → ⚙️ → Install Plugin from Disk… → select the zip → Restart.
