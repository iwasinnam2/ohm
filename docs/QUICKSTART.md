# Quickstart

Change one base URL (or one Cursor attach). Keep your keys and SDKs.

## Design-partner path

1. Email `partners@withohm.dev` (or operator issues `POST /v1/admin/tenants`). Keys use legacy prefix `sk-at-…`.
2. Point your OpenAI SDK at the public edge: `base_url="https://api.withohm.dev/v1"` (or the local edge `http://localhost:8081/v1` for development).
3. Send your provider key as **`X-Ohm-Upstream-Key`** on cache misses (BYOK). Authorization stays your Ohm key.
4. After a week, check `GET /v1/usage` for `cache_hit_ratio`, `fetches`, and `web_context_attach_rate`.
5. Accept Terms/DPA (`terms_ack` / `dpa_ack`) for web context — see [LEGAL.md](LEGAL.md).

## Self-serve

[withohm.dev/billing/intermediate](https://withohm.dev/billing/intermediate) → Checkout ($0 membership + meters) → withOhm key once → card on file.

## Ten lines of Python (BYOK)

```python
from at_utility_sdk import openai_client, LOCAL_BASE_URL

client = openai_client(
    "sk-at-dev",
    base_url=LOCAL_BASE_URL,
    upstream_api_key="sk-proj-...",  # your OpenAI/Anthropic key
)

r = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(r.choices[0].message.content)
```

Identical second call → Redis cache hit (header `x-at-cache: HIT`) — no upstream key needed on hits.

## curl

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

Mock (no upstream key):

```bash
curl -s http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
```

## TypeScript

```ts
import OpenAI from "openai";
import { openaiArgs, LOCAL_BASE_URL } from "@at-utility/sdk";

const client = new OpenAI(
  openaiArgs("sk-at-dev", LOCAL_BASE_URL, { upstreamApiKey: process.env.OPENAI_API_KEY })
);
```

## Cursor

See [CURSOR.md](CURSOR.md) for MCP attach.

See [sdks/](../sdks/) for publish paths. Package rename to `@ohm/sdk` is deferred until first npm publish.
