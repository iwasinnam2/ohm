# Ohm (withOhm)

AI traffic control plane: OpenAI-compatible ingress, Redis prompt replay, compliant web ingest, SSO org tenancy, and a corporate clean ledger — the entropy organizer for enterprise AI chaos. Cursor/MCP are optional clients.

> Point any OpenAI-compatible client (or the Ohm Agent Shell) at one base URL. Keep your keys or use a managed pool. Rent the plumbing; govern the chaos.

**Site:** https://www.withohm.dev · **API:** https://api.withohm.dev/v1 · **Workbench:** `/workbench` · **Vision:** [`docs/VISION.md`](docs/VISION.md) · **Enterprise:** [`docs/ENTERPRISE_CHAOS.md`](docs/ENTERPRISE_CHAOS.md) · **Gem:** [`docs/GEM_POSITION.md`](docs/GEM_POSITION.md)

**License:** MIT (see [`LICENSE`](LICENSE) + [`NOTICE`](NOTICE)). Source is open; the hosted withOhm pipe remains a commercial metered service. Package/key names may still say `at-utility` / `sk-at-*` (legacy AT prefix); the product is **withOhm**.

## Local developer contract (stable)

| Role | Address | Notes |
|------|---------|--------|
| **Public client entry** | `http://localhost:8081/v1` | Rust edge. Point OpenAI software development kits here. |
| **Internal control plane** | `http://localhost:8080` | Python FastAPI. Rust proxies here on cache miss. Do not give this to strangers. |
| **Authentication** | `Authorization: Bearer <ohm-api-key>` | Local bootstrap key: `sk-at-dev` (see `.env`). |
| **BYOK** | `X-Ohm-Upstream-Key: <provider-key>` | Required on cache miss for gpt/claude unless env/enterprise managed keys. |
| **Model selection** | JSON field `model` | `mock` stays local; `gpt-*` / `o*` → OpenAI; `claude-*` → Anthropic. |

```python
from at_utility_sdk import openai_client, LOCAL_BASE_URL

client = openai_client(
    "sk-at-dev",
    base_url=LOCAL_BASE_URL,
    upstream_api_key="sk-proj-...",
)
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Quick start (Docker Compose)

```powershell
cd C:\Users\markk\OneDrive\Documents\at-utility
copy .env.example .env
# Edit .env: set OPENAI_API_KEY for local env-fallback; keep OPENAI_BASE_URL=https://api.openai.com/v1
docker compose --profile rust up --build -d
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\release_smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\railgun_smoke.ps1
```

Release smoke asserts health, mock miss/hit, OpenAI miss/hit (when a key is present), Rust plane header, and usage counters. Railgun smoke asserts BYOK headers, `seat_plus_meters`, and checkout endpoint shape.

## Cursor / MCP

Local **stdio** MCP (remote URL MCP is not shipped). Public base: `https://api.withohm.dev/v1`. Partners: [docs/LAUNCH_GTM.md](docs/LAUNCH_GTM.md) · https://www.withohm.dev/design-partners

```powershell
pip install withohm-mcp
# monorepo dev alternative: pip install -e ".[mcp]"
# Set OHM_API_KEY (required). Optional: OHM_UPSTREAM_KEY, OHM_BASE_URL
# Plugin: .cursor-plugin/ + mcp.json — see docs/CURSOR.md
```

## Streaming and failover honesty

- **Non-streaming** chat completions: the Rust edge may retry the Python upstream (primary then fallback URL) before returning a body. Cache writes happen after a successful full response.
- **Streaming** chat completions: the edge forwards the upstream token stream chunk-by-chunk (no buffering at the edge). Mid-stream provider handoff without a client reconnect is **not** supported. Plan for reconnect or non-stream until that work lands.

## Environment rules

- Live secrets belong only in `.env` (gitignored).
- `.env.example` must never contain a live OpenAI or Stripe secret.
- After changing `.env`, recreate containers: `docker compose up -d --force-recreate gateway`.
- `OPENAI_BASE_URL` must be `https://api.openai.com/v1`, never the website host `platform.openai.com`.

## Legal bounds (mandatory)

Web ingestion is **public-only** and purpose-limited under UK GDPR/CMA and US CFAA/CCPA norms. The whole repo must stay inside this framework—see **[docs/LEGAL.md](docs/LEGAL.md)**.

When `fetch_web_context` is true, clients must send:

- `web_purpose` — one of `public_web_retrieval`, `business_catalog`, `public_company_info`, `job_listings`
- `web_compliance_ack: true` — confirm public-only, no lead harvest / dossiers / gated access
- `terms_ack` / `dpa_ack: true` — bind [docs/legal/](docs/legal/) templates
- optional `cache_control: "no_store"` — skip Redis write for confidential prompts

Inspect live policy: `GET /v1/compliance/policy`. Templates: Terms, DPA, upstream checklist under `docs/legal/`.

## Architecture

| Layer | Role |
|-------|------|
| `gateway-rs` (`:8081`) | Public edge: Redis serialization protocol cache, proxy, plane header |
| Python gateway (`:8080`) | OpenAI-compatible API, providers, rate limits, metering, tenancy, compliance gates |
| Ingest worker (`:8090`) | Meta-search + public page fetch → redacted markdown/JSON for `fetch_web_context` |
| `src/at_utility/compliance/` | Purpose matrix, URL gate, robots.txt, PII redaction |
| `src/ohm_mcp/` | Cursor MCP attach (`ohm_fetch_web`, `ohm_usage`, `ohm_chat`) |
| Redis leader / replica | Cache + RL; GET on replica/reader, SET on leader — [docs/REDIS_MESH.md](docs/REDIS_MESH.md) |
| `infra/` | Terraform + Kubernetes: single-region EKS (mesh retained behind flags) |
| `site/` | Marketing + docs + self-serve `/billing` |

## Tenancy and billing

Bootstrap key `sk-at-dev` works locally. Self-serve: `POST /v1/billing/checkout` (site `/billing`). Ops: issue with admin key (`AT_ADMIN_API_KEYS`):

```powershell
curl.exe -s -X POST http://localhost:8080/v1/admin/tenants `
  -H "Authorization: Bearer sk-at-dev" `
  -H "Content-Type: application/json" `
  -d "{\"plan\":\"payg\",\"label\":\"design-partner-1\",\"terms_ack\":true,\"dpa_ack\":true}"
```

Suspended tenants (`POST /v1/admin/tenants/{id}/status` with `{"status":"suspended"}`, or Stripe cancel webhook) receive HTTP 403.

Metering writes durable daily ledger keys and syncs Stripe Billing Meters when `stripe_customer_id` is set (`ohm_web_fetch`, `ohm_cache_hit`, `ohm_cache_miss`).

**Ledgers:** Customer pays providers (BYOK). Customer pays Ohm seat + meters. Optional: `pip install -e ".[billing]"`.

## Tests

```powershell
pip install -e ".[dev,billing]"
pytest -q
```
