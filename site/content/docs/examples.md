# Drop-in examples

Ohm’s distribution channel is the OpenAI-compatible API. No new protocol.

Keys use legacy prefix `sk-at-…`. Prefer **local edge** until public API cutover. Templates: LangChain / Vercel AI SDK under `examples/templates/` (see [PLATFORM](https://withohm.dev/docs) / repo `docs/PLATFORM.md`).

## Local (supported MVP)

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

## Production host (reserved)

`https://api.withohm.dev/v1` is the documented public hostname (ACM issued). Chat traffic waits on AWS cutover — do not treat HTML on that host as the API.

## Web context (compliance required)

Requires `web_purpose` and `web_compliance_ack`, plus Terms/DPA acks. See [legal](./legal).

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Summarize"}],"fetch_web_context":true,"web_urls":["https://example.com"],"web_purpose":"business_catalog","web_compliance_ack":true,"terms_ack":true,"dpa_ack":true}'
```
