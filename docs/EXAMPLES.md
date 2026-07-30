# Drop-in examples

Ohm’s distribution channel is the OpenAI-compatible API. No new protocol.

Public edge is live at `https://api.withohm.dev/v1`; use the local edge for development. Publish SDKs per [PLATFORM.md](PLATFORM.md).

## Local (supported MVP)

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8081/v1", api_key="sk-at-dev")
```

## TypeScript

```ts
import OpenAI from "openai";
const client = new OpenAI({
  apiKey: "sk-at-dev",
  baseURL: "http://127.0.0.1:8081/v1",
});
```

## Framework templates

- LangChain: [`examples/templates/langchain_openai_base.py`](../examples/templates/langchain_openai_base.py)
- Vercel AI SDK: [`examples/templates/vercel_ai_sdk.ts`](../examples/templates/vercel_ai_sdk.ts)

## curl

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
```

## Web context (compliance required)

Public pages only. See [LEGAL.md](LEGAL.md).

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Summarize"}],"fetch_web_context":true,"web_purpose":"business_catalog","web_urls":["https://example.com"],"web_compliance_ack":true,"terms_ack":true,"dpa_ack":true}'
```

### JSON scrape (`web_format` / ingest `format`)

Structured output: `url`, `title`, `text`, optional `meta` / `json_ld`.

```bash
curl -s http://localhost:8090/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com"],"format":"json","purpose":"public_web_retrieval","compliance_ack":true}'
```

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Extract facts"}],"fetch_web_context":true,"web_format":"json","web_purpose":"public_web_retrieval","web_urls":["https://example.com"],"web_compliance_ack":true,"terms_ack":true,"dpa_ack":true}'
```

Via Cursor MCP: `ohm_fetch_web(urls=[...], format="json")`. See [CURSOR.md](CURSOR.md).

## Later listings

PyPI / npm / directory listings — after public API smoke. See [PLATFORM.md](PLATFORM.md).
