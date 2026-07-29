# Brand

**Product name:** withOhm  
**Logo:** Ω  
**Category:** AI traffic utility / model ingress — not a wrapper.

> Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.

## Hosts

| Host | Role |
|------|------|
| `withohm.dev` / `www` | Marketing + docs |
| `api.withohm.dev` | Reserved public API hostname (ACM issued); edge cutover separate from docs hosting |
| `status.withohm.dev` | Status page |

## Naming debt (intentional)

| Public | Interim / internal |
|--------|---------------------|
| withOhm | Python package `at_utility`, k8s/Terraform `at-utility` |
| Customer keys | Prefix `sk-at-*` until dedicated rename |
| Cache / plane headers | `X-AT-*` until dedicated rename |
| Upstream BYOK | `X-Ohm-Upstream-Key` |

Primary channels: OpenAI-compatible `base_url` swap + [Cursor / MCP attach](/docs/cursor).
