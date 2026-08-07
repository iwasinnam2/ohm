# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **Ohm (withOhm)** monorepo — a metered **pipe** (exact-match
replay + compliant fetch) between apps and LLM providers. “Tollbooth” is the
same idea: you rent the plumbing, not the model. See `README.md` and `docs/`
for product/architecture details; standard commands live in `README.md`,
`pyproject.toml`, `docker-compose.yml`, and `site/package.json`. Lead metaphor
on marketing surfaces is **pipe / pipe rent** ([docs/BRAND.md](docs/BRAND.md)).
The notes below are the non-obvious things for running it in this cloud environment.

### Cloud Agent Builds

Repo-managed env config lives in [`.cursor/environment.json`](.cursor/environment.json)
(Dockerfile base + `install` + `start`). Cursor **Builds** clone the repo and run `install`
ahead of agent starts (formerly the dashboard “update script”). Redis is started via
`start` (disk-only Builds do not keep processes). Do not put `uvicorn` / `npm run dev` /
gateway binaries in `install` — start those when testing (see table below).

### Services (local / cloud agents run them natively, not via Docker Compose)

| Service | Dir | Dev command | Port | Notes |
|---------|-----|-------------|------|-------|
| Python gateway (control plane) | repo root | `uvicorn at_utility.main:app --reload --port 8080` | 8080 | FastAPI, OpenAI-compatible. Docs at `/docs`. |
| Rust edge (public entry) | `gateway-rs/` | `./target/debug/at-gateway-rs` (see env below) | 8081 | Public client entry `:8081/v1`; proxies to Python on cache miss. |
| Ingest worker | repo root | `python -m workers.ingest_worker` | 8090 | Playwright chromium (falls back to httpx). POST `/v1/ingest` needs `purpose` (e.g. `public_web_retrieval`) + `compliance_ack`. |
| Redis | — | `redis-server --port 6379` | 6379 | Cache + rate-limit + metering + tenant store. |
| Site (Next.js) | `site/` | `npm run dev` | 3000 | Marketing/docs/billing. `/billing` → `/subscriptions`. |

Docker Compose (`docker compose --profile rust up`) is the documented path, but Docker is
**not** installed here; run the services natively as above.

### Environment gotchas

- **Python uses a virtualenv at `.venv`.** System pip is PEP 668 externally-managed — always
  `source .venv/bin/activate` (or call `.venv/bin/<tool>`) before `pytest`/`uvicorn`/`python`.
- **`.env` (gitignored) is required.** Copy from `.env.example`. The example ships Docker
  Compose service hostnames; for native dev, `REDIS_URL`/`REDIS_WRITE_URL`/`REDIS_RL_URL` must
  point to `redis://127.0.0.1:6379/0` and `INGEST_WORKER_URL` to `http://127.0.0.1:8090`.
- **Bash-sourcing `.env`:** `AT_COMPLIANCE_USER_AGENT` contains parentheses. Quote its value
  (e.g. `AT_COMPLIANCE_USER_AGENT="OhmBot/0.1 (...)"`) before `set -a; source .env`, or load
  via Python/`uvicorn` dotenv instead. Unquoted values break shell startup with
  `syntax error near unexpected token '('`.
- **Optional secrets (Stripe, Neon `DATABASE_URL`, upstream BYOK):** not required for local
  smoke. Without them, billing checkout returns 503 / meters stay `stripe_synced: false`,
  Postgres mirror stays off, and `model: mock` still proves cache + usage end-to-end.
- **Redis must be running** for the full stack. Without it the gateway silently falls back to
  an in-process `MemoryStore` (cache/metering won't be shared across processes or the Rust edge).
- **Rust edge env** (native run): `AT_RS_LISTEN=0.0.0.0:8081 AT_RS_REDIS=127.0.0.1:6379
  AT_RS_REDIS_WRITE=127.0.0.1:6379 AT_RS_PRIMARY=http://127.0.0.1:8080
  AT_RS_FALLBACK=http://127.0.0.1:8080 AT_API_KEYS=sk-at-dev`. The bootstrap key `sk-at-dev` is
  accepted at the edge via `AT_API_KEYS` and its `tenant_bootstrap_*` id matches the Python
  side, so cache keys line up between the two planes.
- **Rust toolchain:** the build needs a modern Rust (a transitive dep requires `edition2024`).
  A `stable` toolchain (1.97+) is installed via rustup and set as default; the shipped
  `rustc 1.83` in the base image is too old.
- **Models:** `model: "mock"` runs fully offline. `gpt-*`/`claude-*` require BYOK via the
  `X-Ohm-Upstream-Key` header (or `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` in `.env` for env
  fallback). Stripe billing is optional locally and degrades gracefully.

### Auth / smoke test

Public entry is `http://localhost:8081/v1`, bearer `sk-at-dev`. Quick end-to-end check
(mock cache MISS then HIT, then metered usage):

```bash
curl -s -X POST http://127.0.0.1:8081/v1/chat/completions \
  -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
curl -s http://127.0.0.1:8081/v1/usage -H "Authorization: Bearer sk-at-dev"
```

### Tests / lint

- Python tests: `pytest -q` (from repo root, venv active) — asyncio auto mode, `tests/`.
- `site` lint (`npm run lint`) currently **fails** on a pre-existing config issue:
  `site/eslint.config.mjs` imports `eslint-config-next/core-web-vitals` (and `/typescript`)
  without a `.js` extension, which Node 22 ESM cannot resolve because `eslint-config-next@15.5.9`
  ships no `exports` map. This is unrelated to environment setup; build/dev/test are unaffected.
- There is no configured Python linter (no ruff/flake8 in `dev` extras).
