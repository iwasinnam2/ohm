# Enterprise chaos governor

withOhm is the control plane for enterprise AI chaos — SSO, clean ledger,
compliance policy, and the Agent Shell. Cursor is optional.

Full thesis: see the repo doc `docs/ENTERPRISE_CHAOS.md`.

## Surfaces

- [Org console](/org) — cost centers, ledger export, audit
- [Agent Shell](/workbench) — chat only through the Ohm pipe
- [Enterprise apply](/billing/enterprise) — $2,500/mo SKU

## API (short)

```text
POST /v1/org                         create org + bind key
GET  /v1/org/ledger                  summary + events
GET  /v1/org/ledger/export?format=csv
PUT  /v1/org/policy                  model allowlist, purposes
GET  /v1/org/audit
POST /v1/org/sso/dev-login           local SSO (dev secret)
```
