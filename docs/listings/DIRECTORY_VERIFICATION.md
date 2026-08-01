# cursor.directory verification packet

Plugin **ohm** / **withOhm** published to cursor.directory.  
Repo: https://github.com/iwasinnam2/ohm

Use this when a reviewer asks for security / data-handling evidence.

## What was published

Open Plugins package (`.cursor-plugin/`):

- 1× MCP server (`ohm-mcp` stdio)
- Skills: ohm-chat, ohm-fetch-web, ohm-usage, ohm-savings, ohm-models, ohm-providers, ohm-policy (+ docs-context-packer)

Product thesis (not Cursor-only): [ENTERPRISE_CHAOS.md](../ENTERPRISE_CHAOS.md)

## Security answers (short)

| Question | Answer |
|----------|--------|
| Does it phone home? | Yes — only to `OHM_BASE_URL` (default `https://api.withohm.dev/v1`) for chat/fetch/meters |
| Remote MCP? | **No** — local stdio process |
| Where do keys live? | User’s MCP env vars; Ohm stores tenant key **hashes** server-side |
| Training on prompts? | **No** — cache is identical-request replay only (`assert_cache_training_denied`) |
| Web scrape gated? | Yes — purpose, robots, SSRF/URL gate, PII redact ([SECURITY.md](../SECURITY.md)) |
| Open source? | MIT plugin + gateway; hosted pipe is commercial ([NOTICE](../../NOTICE)) |

## Legal links

- Privacy: https://www.withohm.dev/docs/privacy  
- Terms: https://www.withohm.dev/docs/terms  
- Security: https://www.withohm.dev/docs/security  
- Support: partners@withohm.dev  

## Install for reviewers

```bash
pip install withohm-mcp
# MCP env:
#   OHM_API_KEY=<issued seat key>
#   OHM_BASE_URL=https://api.withohm.dev/v1
#   OHM_UPSTREAM_KEY=<optional BYOK>
```

Issue a throwaway Intermediate key at https://www.withohm.dev/billing/intermediate  
(or ask `partners@withohm.dev` for a design-partner seat).

Smoke:

```text
ohm_policy()
ohm_models()
ohm_chat(prompt="ping", model="mock")
```

## Manifest honesty

| Claim | File |
|-------|------|
| Description / keywords | `.cursor-plugin/plugin.json` |
| MCP command | `.cursor-plugin/mcp.json` → `ohm-mcp` + `${OHM_*}` env |
| No committed secrets | `.env` gitignored; `.env.example` placeholders only |
| License | `LICENSE` MIT |

## Post-publish ops

- [x] Listing submitted on cursor.directory  
- [ ] Confirm listing page shows chaos-governor description (edit if scan was stale)  
- [ ] Merge/push plugin metadata to default branch so Re-scan matches  
- [ ] Keep `partners@withohm.dev` monitored for reviewer questions  
