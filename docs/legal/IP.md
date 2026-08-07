# Intellectual property — withOhm / Ohm

**Status:** Operator playbook (not legal advice). Engage counsel before filings.  
**Contacts:** `partners@withohm.dev` · `admin@withohm.dev`  
**Related:** [INVENTION_DISCLOSURE.md](INVENTION_DISCLOSURE.md) · [COPYRIGHT_REGISTRATION.md](COPYRIGHT_REGISTRATION.md) · [NOTICE](../../NOTICE) · [LICENSE](../../LICENSE)

## Dual posture (read this first)

| Layer | What it is | How it is protected |
|-------|------------|---------------------|
| **Open-source repository** | Gateway, edge, SDKs, docs, site source | **Copyright** owned by Ohm / withOhm; licensed to the public under **MIT** ([LICENSE](../../LICENSE)) |
| **Hosted pipe** | `api.withohm.dev`, managed Redis/mesh, billing, keys | Contract (ToS/DPA) + trade secrets in ops; MIT source ≠ free hosted access ([NOTICE](../../NOTICE)) |
| **Brand** | **withOhm**, **Ohm**, Ω mark, `withohm.dev` | **Trademark** + domain (register; do not rely on © alone) |
| **Methods** | Exact-replay tollbooth, cache trees + pipeline metering, purpose-gated compliant ingest | **Patent** candidates — counsel + provisional ASAP (public docs already disclose architecture) |

MIT does **not** dedicate patents or trademarks. It grants copyright permission to use the *software*. Patents (if obtained) and trademarks remain separately assertable unless you later add an express patent grant.

## Immediate checklist (owner actions)

Do these outside the repo; this document only tracks them.

### A. Copyright (automatic + registration)

1. Confirm **legal entity name** that owns the copyright (sole trader / Ltd / LLC). Update `LICENSE`, `NOTICE`, and registration forms to that exact name.
2. File **US Copyright Office** registration for the software + site (see [COPYRIGHT_REGISTRATION.md](COPYRIGHT_REGISTRATION.md)). Registration unlocks statutory damages / attorney fees in US infringement suits.
3. Optionally file **UK** copyright evidence pack (deposit + dated hashes) even though UK © is automatic.
4. Keep **provenance**: git history, contributor agreements / CLA or “work made for hire,” and a dated `NOTICE`.

### B. Patent (time-sensitive)

1. Send [INVENTION_DISCLOSURE.md](INVENTION_DISCLOSURE.md) to a patent attorney **this week**.
2. Decide **US provisional** (cheap date-stamp) vs full non-provisional / PCT — counsel chooses claim strategy.
3. **Grace period warning:** much of the architecture is already public on GitHub and `www.withohm.dev`. US inventors often have a **1-year** grace period from first public disclosure; many other countries (EPO, etc.) are **absolute novelty**. Do not wait.
4. Do **not** put “Patent pending” on the marketing site until a provisional or application serial number exists.
5. After filing, update this doc with application numbers (keep claim text out of the public repo).

### C. Trademark

1. Clear searches: USPTO TESS, UKIPO, EUIPO for **withOhm**, **Ohm** (class 42 software / SaaS), and Ω stylized.
2. File intent-to-use or use-based applications in primary markets (US + UK first).
3. Use marks as adjectives: “the withOhm pipe,” not “a Withohm.”
4. Add ® only after registration; use ™ meanwhile on site footer / brand kit.

### D. Trade secrets (keep out of git)

Never commit: production Redis dumps, customer keys, Stripe live secrets, unpublished claim charts, counsel memos, competitive claim matrices. Prefer encrypted counsel share / Notion private / 1Password vault.

## Repo hygiene (already / keep doing)

| Artifact | Role |
|----------|------|
| `LICENSE` | MIT grant + © line |
| `NOTICE` | © + hosted-service carve-out + trademarks |
| `docs/legal/TERMS_OF_SERVICE.md` | Customer license to *use the Service*; Ohm retains Service IP |
| `docs/LEGAL.md` | Compliance for *fetched third-party content* (not Ohm’s own IP) |
| `src/at_utility/compliance/copyright.py` | Excerpt caps — third-party © minimisation on ingest |

## What MIT still allows competitors to do

Anyone may run, fork, and commercialize **this codebase** under MIT. Differentiation and enforcement lean on:

- Hosted reliability + keys + Stripe meters customers already trust
- Trademark (name/Ω confusion)
- Patents on *methods* (if granted — independent of MIT copyright license)
- ToS bans on extracting cache for competing model training

If you later want a **proprietary** or **source-available** license for new modules, that is a separate product decision — do not silently re-license published MIT commits.

## Filing tracker (fill in)

Linear: [OHM-14 copyright](https://linear.app/withohm/issue/OHM-14/ip-us-copyright-registration-software-site) · [OHM-12 patent](https://linear.app/withohm/issue/OHM-12/ip-patent-counsel-uspto-provisional-exact-replay-tollbooth) · [OHM-13 trademark](https://linear.app/withohm/issue/OHM-13/ip-trademark-clearance-file-withohm-ohm-w)

| Asset | Office | Serial / reg. # | Filed | Counsel | Status |
|-------|--------|-----------------|-------|---------|--------|
| Copyright — software | USCO | | | | pending (OHM-14) |
| Copyright — site / docs | USCO | | | | pending (OHM-14) |
| Provisional patent | USPTO | | | | pending disclosure (OHM-12) |
| Trademark — withOhm | USPTO | | | | pending search (OHM-13) |
| Trademark — withOhm | UKIPO | | | | pending search (OHM-13) |
| Trademark — Ω device | | | | | pending (OHM-13) |

## Counsel packet (attach)

1. This file + invention disclosure + copyright registration checklist  
2. `docs/ARCHITECTURE.md`, `docs/CACHE_TREES.md`, `docs/LEGAL.md`  
3. Live URLs: `https://www.withohm.dev`, `https://api.withohm.dev`  
4. First public disclosure dates (git tags / Amplify go-live / Show HN — as applicable)  
5. Inventor legal names and citizenship / residency  

---

*Not legal advice. Operators remain responsible for filings and jurisdictions.*
