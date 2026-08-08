# API reference (index)

Public base: `https://api.withohm.dev/v1`. OpenAI-compatible chat is the primary contract.

## Essentials

| Area | Endpoints / notes |
|------|-------------------|
| Chat | `POST /v1/chat/completions` — BYOK, optional `X-Ohm-Cache-Tree`, path headers |
| Cache trees | `GET/POST /v1/cache/trees`, `.../reset`, `.../promote`, `.../freeze` |
| Usage | `GET /v1/usage` |
| Savings | `GET /v1/savings` — always `estimate_only` |
| Honesty | `GET /v1/public/honesty` |
| Stats | `GET /v1/public/stats` |
| Health | `GET /health`, `GET /ready` |
| JWKS | `/.well-known/http-message-signatures-directory` |

## Headers that matter

- `Authorization: Bearer sk-at-…` — legacy prefix; brand is withOhm. A `sk-ohm-` cutover is planned and will be announced before rename.
- `X-Ohm-Cache-Tree` — named inventory (header wins over body `cache_tree`)
- `X-Ohm-Path` — cost-center / path attribution
- Provider BYOK headers per [Quickstart](/docs/quickstart)

## Examples

- [Drop-in examples](/docs/examples)
- [Command catalog (MCP)](/docs/commands)
- [Cache trees](/docs/cache-trees)
- [Receipts](/docs/receipts)
