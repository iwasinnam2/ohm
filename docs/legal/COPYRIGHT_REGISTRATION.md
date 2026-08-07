# Copyright registration checklist — withOhm / Ohm

**Not legal advice.** US registration strengthens enforcement; copyright in the US and UK exists automatically on fixation. Use this as an operator checklist for counsel or self-filing via copyright.gov.

## What to register

| Work | Suggested title on form | Nature of work | Deposit |
|------|-------------------------|----------------|---------|
| Gateway + edge + workers | `Ohm / withOhm — AI traffic utility source code` | Computer program | Source code deposit (see below) |
| Marketing / docs site | `withOhm website and documentation (www.withohm.dev)` | Literary / audiovisual (text + UI) | PDF or ZIP of public pages + `site/` content |
| Brand assets (optional separate) | `Ohm Ω icon and brand kit` | Visual art | `brand/ohm-icon.svg`, PNGs |

Register **software** and **site** as separate applications if counsel prefers clearer remedies.

## Copyright claimant

Use the **exact legal name** of the owning person or company (same string in `LICENSE` / `NOTICE`). If the repo currently says `Ohm / withOhm`, replace with the entity that should own the rights (e.g. `WithOhm Ltd`, `… LLC`) before filing.

If contractors or agents contributed code: obtain written assignment or confirm work-made-for-hire before listing a single claimant.

## United States (copyright.gov)

1. Create / sign in at [copyright.gov](https://www.copyright.gov/) → **Register** → Standard Application.
2. Type of work: **Computer Program** (code) or **Literary Work** (docs/site prose).
3. Author: legal name(s); citizenship; “work made for hire” if company is author.
4. Claimant: owning entity.
5. Year of completion: **2026** (or first substantial fixation year).
6. Date of first publication: date the repo or site was first made available to the public (git / Amplify). If unpublished, say so.
7. Limitation of claim: if you used MIT/third-party libraries, exclude material not owned (or rely on dependency licenses; do not claim Apache/MIT upstream code as yours).
8. **Deposit (computer program):**
   - Preferred: first 25 and last 25 pages of source **or** the entire program if <50 pages.
   - Trade-secret option: blocked-out portions of deposit per Circular 61 — discuss with counsel if you want to hide secrets (most of this repo is already public MIT, so full public deposit is usually fine).
   - Practical pack: ZIP of `src/`, `gateway-rs/src/`, `workers/`, `LICENSE`, `NOTICE`, and a `MANIFEST.txt` listing commit SHA.
9. Pay fee; record **case / registration number** in [IP.md](IP.md) filing tracker.
10. Keep confirmation email + certificate PDF in counsel vault (not necessarily in git).

### Deposit helper (generate locally)

```bash
# From repo root — for counsel ZIP, not committed:
git rev-parse HEAD > /tmp/ohm-copyright-manifest.txt
git log -1 --format='%H %cI %s' >> /tmp/ohm-copyright-manifest.txt
zip -r /tmp/ohm-copyright-deposit.zip \
  LICENSE NOTICE README.md \
  src gateway-rs/src workers \
  docs/ARCHITECTURE.md docs/CACHE_TREES.md docs/legal \
  -x '*.pyc' -x '*/target/*' -x '*/node_modules/*'
```

## United Kingdom

UK copyright is automatic; there is no mandatory government register equivalent to USCO for these works. Still:

1. Keep dated evidence: git tags, Amplify deploy logs, this deposit ZIP + SHA-256.
2. Optionally use a solicitor deposit / escrow or trusted timestamp for evidentiary weight.
3. Database right may separately protect substantial investment in structured caches — product stance is **identical-request replay**, not a publishable training corpus; counsel should review ToS §4–6.

## Notices to keep in-repo

- `LICENSE` — MIT + `Copyright (c) YEAR OWNER`
- `NOTICE` — ownership + hosted carve-out + trademarks
- Optional file headers on new substantial modules:

```text
Copyright (c) 2026 Ohm / withOhm. SPDX-License-Identifier: MIT
```

Do not strip copyright notices from forks you distribute.

## After registration

1. Update [IP.md](IP.md) tracker with registration numbers.  
2. Optionally add to `NOTICE`: `US Copyright Registration No. …` (only after certificate issues).  
3. Enforcement: DMCA for hosted infringing copies of *your* site assets; MIT still allows others to run the *code* — registration does not cancel the MIT grant on published versions.
