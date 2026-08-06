# Enterprise product pack

Commercial + technical delivery for `enterprise-dedicated-pool` (listed as contact us; negotiated).
Thesis: [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

## Delivered in product

| Capability | Surface |
|------------|---------|
| Org model | `POST /v1/org`, `GET /v1/org` |
| Cost centers | `PUT /v1/org/cost-centers` |
| Clean ledger | `GET /v1/org/ledger`, `GET /v1/org/ledger/export` |
| Monthly statement | `GET /v1/org/ledger/statement?month=YYYY-MM` |
| Hit-ratio inventory | `GET /v1/org/ledger/hit-ratio?month=YYYY-MM&group_by=cost_center\|path` |
| Spend caps | Org policy `spend_cap_usd_month` / `spend_cap_mode` / `spend_caps_by_cost_center` |
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

## FinOps export contract

**Monthly statement** — chargeback-grade summary for one UTC calendar month:

```http
GET /v1/org/ledger/statement?month=2026-08
Authorization: Bearer sk-at-…
```

Response fields (selected):

| Field | Meaning |
|-------|---------|
| `month` / `since_ts` / `until_ts` | UTC month window `[since, until)` |
| `by_cost_center` | Pipe rent + estimated provider avoided per center |
| `by_path` | Same shape by frequency-farm path (`X-Ohm-Path`) |
| `pipe_rent_usd` | Billable Ohm meters for the window |
| `estimated_provider_avoided_usd` | Blended list estimate on **cache hits only** |
| `cache_hits` / `cache_misses` / `fetches` | Event counts |
| `estimate_only` | Always `true` until invoice import lands |

**Hit ratio** — inventory by cost center or path for one UTC month:

```http
GET /v1/org/ledger/hit-ratio?month=2026-08&group_by=path
Authorization: Bearer sk-at-…
```

**Spend caps** — meter pipe rent USD this UTC month per cost center; evaluated
on cache **MISS** before upstream. Soft: allow + `X-Ohm-Spend-Cap` headers /
audit `org.spend_cap_soft`. Hard: `402` `spend_cap_exceeded` / audit
`org.spend_cap_hard`. HITs always serve. Caps ≠ prepaid credits.

**CSV for the same window:**

```http
GET /v1/org/ledger/export?format=csv&month=2026-08
```

Org console: https://www.withohm.dev/org — **This month statement** + **Download month CSV**.

Not in this slice: provider invoice import / true reconcile (`provider_invoice_import_usd` stays null). FinOps remains `estimate_only`.

## Invoice / PO

Stripe Enterprise Price (`STRIPE_PRICE_ENTERPRISE`) via checkout / sales apply
form. Net terms and MSA countersign are sales-led (`partners@withohm.dev`).

## SLA

`AT_ENTERPRISE_SLA_NOTE` — target 99.9% until countersigned order form. See
SKU `sla_note`.

## SOC 2

Process roadmap: [SOC2_ROADMAP.md](SOC2_ROADMAP.md).
