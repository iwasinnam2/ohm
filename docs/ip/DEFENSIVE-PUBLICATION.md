# Defensive publication checklist (Do-not-file path — 20% allocation)

Use **only** if counsel Traffic Lights are Red / **Do not file**, or after a
filing priority date when you want a public archive citation. File-lean work
does **not** require running this now.

## Goal

A version-pinned, citable snapshot of the public enablement surface so prior
art is easy to point at without relying on “whatever master was that day.”

## Steps (when triggered)

1. Confirm Phase B binary is **Do not file** (or post-priority publication OK).
2. On `master` at the chosen commit, create an annotated tag:
   ```bash
   git tag -a defensive-pub-YYYYMMDD -m "Defensive publication snapshot YYYY-MM-DD"
   git push origin defensive-pub-YYYYMMDD
   ```
3. Export a PDF/zip of at least:
   - `docs/ip/BRIEF.md`
   - `docs/ip/03-GAP-AUDIT.md`
   - `docs/ARCHITECTURE.md`
   - `docs/RECEIPTS.md`
   - `docs/CACHE_TREES.md`
   - `docs/REDIS_MESH.md`
   - `GET /v1/public/honesty` JSON capture (optional)
4. Store the archive off-git (counsel drive / object storage) with the tag SHA.
5. Update [04-DISCLOSURE-INVENTORY.md](04-DISCLOSURE-INVENTORY.md) “Dated snapshot”
   row with tag name + date.

## Do not

- Do not tag while File is still the preferred path and unpublished A4/CAS
  claim material is still being protected.
- Do not treat this checklist as a substitute for counsel advice.

## Current status

**Not done.** File-lean bifurcation prioritizes admit fencing (A4) engineering
over snapshot tagging until Traffic Lights return.
