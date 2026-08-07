# Legal & compliance

withOhm’s web ingestion is **public-only** and purpose-limited. Binding public documents:

- [Terms of Service](./terms) (`tos-2026-07-26`)
- [Privacy Policy](./privacy)
- [Data Processing Addendum](./dpa) (`dpa-2026-07-26`)
- [Copyright & database rights](./copyright) (`copyright-2026-08-07`)
- [Security](./security)

> Not legal advice. Operators and tenants remain responsible for their jurisdictions and use cases.

## Required fields (web context)

When `fetch_web_context` is true:

- `web_purpose`: `public_web_retrieval` | `business_catalog` | `public_company_info` | `job_listings`
- `web_compliance_ack`: `true`
- `terms_ack` / `dpa_ack`: `true` (when enforcement is on)

Optional: `cache_control: "no_store"` to skip Redis cache writes.

## Not allowed

Lead harvesting, person dossiers, biometrics, login-gated or credentialed URLs, cold-email / SMS blast list building, cache export for model training, bulk republication of fetched pages.

## Policy API

`GET /v1/compliance/policy` (authenticated) returns the live matrix, excerpt caps, copyright posture (`copyright` object), ack requirements, and public document URLs.
