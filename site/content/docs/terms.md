# Terms of Service

**Version:** `tos-2026-07-26`  
**Product:** Ohm OpenAI-compatible gateway + optional public-web ingestion  
**Contact:** partners@withohm.dev

By calling the API with `terms_ack: true` (or accepting these terms at tenant issue), you agree to this version.

## 1. Service

Ohm provides: (a) LLM request routing and identical-request cache replay; (b) optional public-web context fetch under the [Legal & compliance](./legal) framework. Upstream model providers process prompts under their terms.

**MVP status:** The marketed hostname may serve documentation while the production edge is brought online. Local and staging contracts remain `localhost:8081` / operator-deployed edges. Mid-stream provider handoff is unsupported — see [Streaming](./streaming).

## 2. Accounts and keys

API keys identify a tenant. You are responsible for key custody. Suspended tenants receive HTTP 403.

**Key prefix:** Issued keys currently use the legacy prefix `sk-at-…` (internal package name `at-utility`). The product brand is **Ohm**; a `sk-ohm-` cutover is deferred and will be announced before rename.

## 3. Prohibited uses

You must not use the Service to:

- Access login-gated, credentialed, or private account systems
- Harvest leads, build person dossiers, or derive biometrics
- Conduct unsolicited direct marketing without a lawful basis (UK PECR and equivalents)
- Violate copyright, database rights, or site terms through bulk republication of fetched content
- Attempt to extract cache contents for model training or competing model development
- Violate applicable computer-misuse / unauthorized-access laws

## 4. Cache

Identical chat requests may be stored in Redis for the configured TTL solely for **identical-request replay**. Cache is not a training corpus. Use `cache_control: "no_store"` when prompts must not be written to cache. Response headers use the legacy family `X-AT-*` until a rename cutover.

## 5. Web ingestion

Requires `web_purpose`, `web_compliance_ack`, and (when enforced) `terms_ack` / `dpa_ack`. Fetched pages are excerpted and personal identifiers are redacted by default. Public pages only.

## 6. Customer content

You retain rights in prompts and outputs as between you and Ohm, subject to upstream provider terms. You grant Ohm a limited license to process content to provide the Service (routing, caching as configured, metering).

## 7. Subprocessors

See [Security](./security) and the [DPA](./dpa).

## 8. Fees and ledgers

Ohm invoices (Stripe) are separate from upstream provider pay-as-you-go costs. Usage meters and savings figures are **estimates** for identical-request cache effects, not guaranteed savings. Enterprise SKU availability does not imply a published uptime SLA until a separate SLA schedule is executed.

## 9. Disclaimer and liability

Service is provided as-available for MVP. Caps and exclusions for a specific deploying entity should be set with that entity’s counsel.

## 10. Acknowledgement

API field `terms_ack: true` and tenant `terms_version` at key issue bind this version (`tos-2026-07-26`).
