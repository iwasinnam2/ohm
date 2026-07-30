# Legal & compliance framework (applied)

Ohm / `at-utility` is designed as a **public-web retrieval + LLM routing** utility—not a lead harvester, account-access tool, or person-dossier engine.

This document binds the **entire repo** (gateway, ingest worker, SDKs, docs, site) to the UK/US online-data framework summarized below. Product defaults enforce these bounds in code under `src/at_utility/compliance/`.

> Not legal advice. Operators and tenants remain responsible for their use cases and jurisdictions.

## Operating principle

| Allowed | Prohibited |
|---------|------------|
| Public `http`/`https` pages a normal browser can open without login | Login walls, credentials in URLs, session/token reuse, private/app hosts |
| AI-search style retrieval with citations | Contact/lead harvesting, people-search dossiers |
| Business catalogs, public company pages, public job ads | Biometrics / face matching from scraped photos |
| PII redaction + robots.txt respect (default on) | Continuing after access revocation or technical blocks |

## Risk matrix (product mapping)

| Target | Default product stance | Purpose enum |
|--------|------------------------|--------------|
| E-commerce / product catalogs | **Go** | `business_catalog` |
| Public company pages | **Go** (org-level; minimise people fields) | `public_company_info` |
| Public job ads (no CVs) | **Go** | `job_listings` |
| General public pages for answers | **Caution** (cite; minimise) | `public_web_retrieval` |
| Public social profile bulk / lead lists | **No-go** | blocked purposes |
| Login-gated / private account data | **No-go** | URL gate + CMA/CFAA |
| Faceprints / biometrics | **No-go** | blocked purposes |

## UK

- **UK GDPR / DPA 2018:** Information relating to an identified or identifiable living person is personal data—even if posted publicly. Ingest therefore **minimises** (redacts emails/phones/IDs by default).
- **Computer Misuse Act 1990:** Unauthorized access to computer material is criminal. Account/app hosts, credentialed URLs, and token-bearing URLs are rejected.
- **Misuse of private information** (*Campbell*): reasonable expectation of privacy can survive partial publicity. Product refuses High/Severe purposes (dossiers, intimate harvesting).
- Controllers using Ohm for UK personal data still need their own lawful basis (often legitimate interests for retrieval)—Ohm is infrastructure, not a blanket LIA.

## United States / California

- **CFAA:** Anti-intrusion statute (*Van Buren* gates-up/down). Public pages ≠ license to bypass auth. Revoked access + continued fetching is out of bounds (*Power Ventures*-type facts).
- **CCPA/CPRA:** “Personal information” is broad; **publicly available** consumer-posted info may be carved out, but that does **not** authorize gated access or biometrics collected without knowledge.
- **Common-law privacy torts:** Weak against voluntarily public facts; stronger against intrusion into private spaces and biometric appropriation. Product stays on the public side of the gate.

## How the code enforces this

| Component | Enforcement |
|-----------|-------------|
| `compliance/policy.py` | Allowed/blocked purposes, ack requirement, query heuristics |
| `compliance/url_gate.py` | Scheme, credentials, private IPs, login/account paths, tokens |
| `compliance/robots.py` | `OhmBot` robots.txt checks (default on) |
| `compliance/pii.py` | Email/phone/ID redaction before context injection |
| `compliance/copyright.py` | Per-source / total excerpt caps; large code-block stripping |
| `compliance/terms.py` | `terms_ack` / `dpa_ack` validation |
| Gateway `POST /v1/chat/completions` | Requires purpose + compliance/terms/dpa acks; `cache_control: no_store` |
| `GET /v1/compliance/policy` | Machine-readable policy for clients (including adjacent flags) |
| Ingest worker `/v1/ingest` | Re-validates; refuses non-compliant fetches with HTTP 403 |

### API contract (web context)

```json
{
  "model": "mock",
  "messages": [{"role": "user", "content": "Summarize this product page"}],
  "fetch_web_context": true,
  "web_urls": ["https://example.com/product/1"],
  "web_purpose": "business_catalog",
  "web_compliance_ack": true,
  "terms_ack": true,
  "dpa_ack": true,
  "cache_control": "no_store"
}
```

Allowed `web_purpose` values: `public_web_retrieval`, `business_catalog`, `public_company_info`, `job_listings`.

`cache_control: "no_store"` skips Redis write (confidential prompts). Default cache purpose is identical-request replay only (`X-AT-Cache-Purpose: identical-request-replay`).

## Adjacent frameworks

Access/privacy gates are necessary but not sufficient. These regimes also bind the product:

| Framework | Product posture | Where |
|-----------|-----------------|-------|
| **Customer terms + DPA** | Controller (tenant) / processor (Ohm); prompts may hit Redis TTL cache | [legal/TERMS_OF_SERVICE.md](legal/TERMS_OF_SERVICE.md), [legal/DPA.md](legal/DPA.md); `terms_ack` / `dpa_ack` |
| **Upstream provider ToS** | Passthrough inference; no Ohm training on tenant prompts | [legal/UPSTREAM_PROVIDERS.md](legal/UPSTREAM_PROVIDERS.md) |
| **Copyright / database right** | Short excerpts for retrieval; per-source and total char caps; no bulk republication | `compliance/copyright.py` |
| **UK PECR / anti-spam** | Blocked purposes: cold email, SMS blast, direct-marketing lists | `compliance/policy.py` |
| **EU GDPR readiness** | Same minimisation + DPA roles; document transfers before EU go-live | DPA template + jurisdiction warnings |
| **Consumer / billing hygiene** | Separate Ohm invoice vs upstream cost; savings are **estimates** | [PRICING.md](PRICING.md), `GET /v1/savings` |

### EU addendum (no product fork)

Default profile remains `uk_us`. For EU tenants: treat personal data under GDPR, complete transfer tooling in the DPA, and keep subprocessors current. DPIAs remain the controller’s duty for high-risk profiling uses (which Ohm blocks at the purpose layer).

## Tenant responsibilities

By setting `web_compliance_ack`, `terms_ack`, and `dpa_ack` as required, the caller confirms:

1. They will use retrieval only for the declared purpose.
2. They will not request login-gated, credentialed, or private-account access.
3. They will not use outputs for lead generation, stalking, biometrics, or unsolicited direct marketing without a lawful basis.
4. They accept the bound Terms and DPA versions and will not use cache contents for model training.
5. They will comply with UK GDPR/CMA, EU GDPR where applicable, and US CFAA/CCPA/state privacy laws, including their own notices and lawful bases.

## Configuration

| Env | Default | Meaning |
|-----|---------|---------|
| `AT_COMPLIANCE_ENFORCE` | `true` | Master switch (keep on in prod) |
| `AT_COMPLIANCE_REQUIRE_ACK` | `true` | Require `web_compliance_ack` |
| `AT_COMPLIANCE_REQUIRE_TERMS_ACK` | `true` | Require `terms_ack` (+ `dpa_ack`) for web context |
| `AT_COMPLIANCE_JURISDICTION` | `uk_us` | Warning/profile set |
| `AT_COMPLIANCE_RESPECT_ROBOTS` | `true` | Honor robots.txt |
| `AT_COMPLIANCE_REDACT_PII` | `true` | Redact common personal identifiers |
| `AT_COMPLIANCE_MAX_CHARS_PER_SOURCE` | `4000` | Copyright excerpt cap per URL |
| `AT_COMPLIANCE_MAX_CONTEXT_CHARS` | `12000` | Total injected web context cap |
| `AT_COMPLIANCE_ALLOW_CACHE_TRAINING` | `false` | Hard-deny cache export for training |
| `AT_COMPLIANCE_TERMS_VERSION` | `tos-2026-07-26` | Bound Terms version at tenant issue |
| `AT_COMPLIANCE_DPA_VERSION` | `dpa-2026-07-26` | Bound DPA version at tenant issue |
| `AT_COMPLIANCE_USER_AGENT` | OhmBot/0.1… | Crawl identification |
| `AT_WEB_BOT_AUTH_ED25519_SEED_B64` | (empty) | Web Bot Auth signing seed (base64 32 bytes); empty disables RFC 9421 signatures |
| `AT_WEB_BOT_AUTH_SIGNATURE_AGENT` | (empty) | Public key-directory URL sent as `Signature-Agent` |

Disabling enforcement is for local experiments only and does **not** change what the law allows.

## Verified crawling & licensed-crawl era (Web Bot Auth / Pay Per Crawl)

OhmBot participates in the permission-based crawl model:

- **Identity**: every fetch sends the OhmBot User-Agent; when a signing seed is
  configured, fetches also carry RFC 9421 HTTP Message Signatures
  (`Signature`, `Signature-Input`, `Signature-Agent`; `tag="web-bot-auth"`) so
  origins and CDNs can verify OhmBot instead of treating it as anonymous.
  The public JWKS is served at `/.well-known/http-message-signatures-directory`.
- **HTTP 402 (pay-per-crawl)**: honored as the origin's licensing decision.
  Ohm does **not** auto-pay; the refusal (with any `crawler-price` signal) is
  surfaced to the caller as `payment_required_402`.
- **HTTP 401/403**: access revocation is honored — no retries, no block
  evasion (`access_denied_401/403`).

## AI search posture

A successful AI search utility must stay inside these laws. Ohm’s compliant lane is:

**crawl/index public pages → retrieve short excerpts with citations → generate with minimisation**

not: private-account access, training on gated corpora without rights, people-intelligence dossiers, or PECR-violating outreach lists.

## Precedents (orientation only)

- UK: CMA s.1; *Allison*; UK GDPR definitions; *Campbell*; *Lloyd v Google* (damages procedure); PECR for marketing.
- US: CFAA; *Van Buren*; *Nosal*; *hiQ* (public scrape CFAA limits in 9th Cir.); *Power Ventures* (revoked access).

Templates: [legal/](legal/). Trust/retention: [SECURITY.md](SECURITY.md).
