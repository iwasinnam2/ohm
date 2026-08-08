# Drop-in examples

withOhm’s distribution channel is the OpenAI-compatible API. No new protocol.

Keys use legacy prefix `sk-at-…`. Public base: `https://api.withohm.dev/v1`. Local edge: `http://localhost:8081/v1`. Templates: LangChain / Vercel AI SDK under `examples/templates/` — see [docs/PLATFORM.md](https://github.com/iwasinnam2/ohm/blob/master/docs/PLATFORM.md) (source is open).

## Local (supported)

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8081/v1", api_key="sk-at-dev")
```

```ts
import OpenAI from "openai";
const client = new OpenAI({
  apiKey: "sk-at-dev",
  baseURL: "http://127.0.0.1:8081/v1",
});
```

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
```

## Production

```python
from openai import OpenAI
client = OpenAI(
    api_key="sk-at-YOUR_OHM_KEY",
    base_url="https://api.withohm.dev/v1",
    default_headers={"X-Ohm-Upstream-Key": "sk-proj-..."},  # BYOK on miss
)
```

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

## Web context (compliance required)

Requires `web_purpose` and `web_compliance_ack`, plus Terms/DPA acks. See [legal](./legal).

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Summarize"}],"fetch_web_context":true,"web_urls":["https://example.com"],"web_purpose":"business_catalog","web_compliance_ack":true,"terms_ack":true,"dpa_ack":true}'
```

### JSON scrape

Structured output: `url`, `title`, `text`, optional `meta` / `json_ld`.

```bash
curl -s http://localhost:8090/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com"],"format":"json","purpose":"public_web_retrieval","compliance_ack":true}'
```

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Extract facts"}],"fetch_web_context":true,"web_format":"json","web_purpose":"public_web_retrieval","web_urls":["https://example.com"],"web_compliance_ack":true,"terms_ack":true,"dpa_ack":true}'
```

Via Cursor MCP: `ohm_fetch_web(urls=[...], format="json")`. See [cursor](./cursor).
