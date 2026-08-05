# SOC 2 Type I roadmap (process, not theater)

Tied to chaos-governor controls already in product: SSO, audit log, org policy,
DPA bind, no training on cache.

## Scope

Security, Availability, Confidentiality — AI traffic control plane
(`api.withohm.dev`, org console, ingest worker).

## Evidence we can collect now

| Control | Evidence |
|---------|----------|
| Access control | OIDC SSO sessions; org roles; API key hashes |
| Audit | `GET /v1/org/audit` append-only log |
| Change management | GitHub PRs + deploy logs |
| Encryption in transit | TLS everywhere (edge + Redis `rediss://`) |
| Vendor management | [docs/legal/UPSTREAM_PROVIDERS.md](legal/UPSTREAM_PROVIDERS.md) |
| Privacy | DPA versions on org/tenant; `assert_cache_training_denied` |

## Sequence

1. Freeze policy docs (this file + LEGAL + ENTERPRISE_CHAOS)
2. Enable production OIDC (Okta/Entra) — disable `AT_SSO_DEV_SECRET`
3. Retain audit + ledger events ≥ 90 days
4. Engage auditor for Type I readiness review
5. Type II after 3–6 months of continuous evidence

No fake “we are SOC2 certified” claims until the report exists.
