# Copyright & database-right policy

**Version:** `copyright-2026-08-07`  
**Product:** withOhm (Ohm) — OpenAI-compatible pipe + public-web ingestion  
**Public mirror:** site `/docs/copyright`  
**Takedown / rights contact:** partners@withohm.dev (subject: `Copyright`)

> Not legal advice. Excerpt caps and technical controls are **minimisation
> measures**, not a fair-use opinion, licensed-crawl certificate, or warranty
> that any particular retrieval is lawful in your jurisdiction.

## 1. What Ohm does **not** claim

- Ohm does **not** own third-party page content fetched for web context.
- Ohm does **not** grant you a bulk republication license, scrape-to-publish
  right, or training-corpus right in fetched material.
- “Compliant fetch” means **purpose-bound public retrieval with technical
  controls** (robots, URL gate, excerpt caps, PII redaction, no cache
  training). It is **not** a certification that your use is copyright-safe.

## 2. What Ohm **does** claim (and enforce)

| Posture | Enforcement |
|---------|-------------|
| Short excerpts for retrieval / identical-request replay | Per-source + total char caps; large code-block stripping (`compliance/copyright.py`) |
| No bulk republication API | ToS §3; ingest returns excerpted context, not full-page mirrors |
| Cache is identical-request replay only — never training | `AT_COMPLIANCE_ALLOW_CACHE_TRAINING=false` hard-deny |
| Public pages only | URL gate + robots fail-closed |
| HTTP 402 pay-per-crawl honored | No auto-pay; no store of 402-denied bodies |
| Operator ceiling on excerpt size | Worker clamps client `max_chars_per_source` to `AT_COMPLIANCE_MAX_CHARS_PER_SOURCE` |

## 3. Software copyright (this repo)

Source under MIT — see root [`LICENSE`](../../LICENSE) and [`NOTICE`](../../NOTICE).
The hosted pipe (`api.withohm.dev`) remains a commercial metered service under
the site Terms.

## 4. Tenant duties

By using web ingest (and by `terms_ack` / `web_compliance_ack`), you agree:

1. You will treat fetched text as **short quotations for your retrieval task**,
   not as a corpus to republish, scrape-to-site, or train models on.
2. You will not ask Ohm to bypass paywalls, 402 licensing gates, or robots
   denials to obtain fuller copies.
3. You remain responsible for your outputs (including model completions that
   may quote context) and for your jurisdiction’s copyright / database-right
   rules.
4. You will not use Ohm cache contents or fetch outputs for model training or
   competing model development.

## 5. Rights-holder / DMCA-style notice

Ohm is infrastructure. If you are a rights holder and believe material
accessible **through** the hosted pipe should be restricted:

1. Email **partners@withohm.dev** with subject `Copyright`.
2. Include: your contact; works identified; URLs concerned; statement of good
   faith; authority to act.
3. We will acknowledge within **3 business days** and, where appropriate,
   suspend offending tenant keys, tighten robots/blocks, or refuse further
   fetches of identified URLs on the hosted service.

This is an operational intake path for the **hosted** service. Self-hosted
operators must publish their own contact.

## 6. Machine-readable surface

`GET /v1/compliance/policy` (authenticated) exposes:

- `adjacent_frameworks` including `copyright_excerpt_caps`
- `copyright` object: policy URL, contact, excerpt caps, output posture
- `allow_cache_training: false`
- `rules` including short-excerpt and no-training lines

## 7. Related

- [LEGAL.md](../LEGAL.md) — full compliance framework  
- [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) §3 — prohibited bulk republication  
- [DPA.md](DPA.md) — no training on Customer Content  
- [UPSTREAM_PROVIDERS.md](UPSTREAM_PROVIDERS.md) — provider ToS  

**Version bind:** documentary only under this `copyright-2026-08-07` tag;
Terms remain `tos-2026-07-26` unless separately bumped.
