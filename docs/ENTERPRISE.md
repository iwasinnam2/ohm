# Enterprise product pack

Commercial + technical delivery for `enterprise-dedicated-pool` ($2,500/mo).
Thesis: [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

## Delivered in product

| Capability | Surface |
|------------|---------|
| Org model | `POST /v1/org`, `GET /v1/org` |
| Cost centers | `PUT /v1/org/cost-centers` |
| Clean ledger | `GET /v1/org/ledger`, `GET /v1/org/ledger/export` |
| Audit log | `GET /v1/org/audit` |
| Org policy | `PUT /v1/org/policy` |
| Service keys | `POST /v1/org/keys` |
| OIDC SSO | `GET /v1/org/sso/authorize`, `POST /v1/org/sso/callback` |
| Dev SSO | `POST /v1/org/sso/dev-login` (`AT_SSO_DEV_SECRET`) |
| SCIM Users | `GET/POST /v1/scim/v2/Users` (enterprise org key) |
| Managed keys | Org policy `managed_keys` + env provider keys |
| Agent Shell | https://www.withohm.dev/workbench |
| Org console | https://www.withohm.dev/org |

SKU catalog: `GET /v1/enterprise/skus` → `delivered` flags.

## Invoice / PO

Stripe Enterprise Price (`STRIPE_PRICE_ENTERPRISE`) via checkout / sales apply
form. Net terms and MSA countersign are sales-led (`partners@withohm.dev`).

## SLA

`AT_ENTERPRISE_SLA_NOTE` — target 99.9% until countersigned order form. See
SKU `sla_note`.

## SOC 2

Process roadmap: [SOC2_ROADMAP.md](SOC2_ROADMAP.md).
