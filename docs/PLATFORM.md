# Platform placement

Ohm distributes as an **OpenAI-compatible `base_url`**. No new protocol.

## Gate

Publish packages and directory listings only after:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey <key>
```

passes (chat miss/hit). Until then, document **local** `http://localhost:8081/v1`.

## Packages (rename deferred)

| Path | Publish name (current) | Target rename |
|------|------------------------|---------------|
| `sdks/typescript` | `@at-utility/sdk` | `@ohm/sdk` |
| `sdks/python` | `at-utility-sdk` | `ohm-sdk` |

```bash
# TypeScript (after public API green)
cd sdks/typescript && npm publish --access public

# Python
cd sdks/python && python -m build && twine upload dist/*
```

## Templates

| Recipe | Path |
|--------|------|
| LangChain custom base | [`examples/templates/langchain_openai_base.py`](../examples/templates/langchain_openai_base.py) |
| Vercel AI SDK | [`examples/templates/vercel_ai_sdk.ts`](../examples/templates/vercel_ai_sdk.ts) |

## Listings (after one public demo)

1. Awesome lists / agent registries — link quickstart + `api.withohm.dev`
2. Framework “custom OpenAI base URL” docs PRs
3. Design-partner case quotes on https://withohm.dev

Do not rename `sk-at` / `X-AT` in the same release as first publish.
