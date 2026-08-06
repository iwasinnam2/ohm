# neon-ohm-ci — Neon × withOhm compose starter

**withOhm — middleware governance.** Exact-replay inventory that branches with the same PR slug as your Neon preview.

Neon owns **database state** (and, in beta, branch-scoped **AI Gateway**).  
withOhm owns **exact-replay inventory** (tips, Promote, HIT meters, receipts).

Compose them. Do not confuse the nouns.

| Peer | Branches | Header / env |
|------|----------|----------------|
| Neon | Postgres state (+ AI Gateway endpoint per branch) | `DATABASE_URL` / Neon branch |
| withOhm | Exact-replay tip | `X-Ohm-Cache-Tree: pr-$N` |

## One-slug discipline

Use the same slug everywhere:

```text
pr-${{ github.event.number }}
```

- Neon preview branch name: `pr-842`
- Ohm cache tip: `pr-842`
- Optional: Neon AI Gateway calls from that branch stay on the preview path; Ohm tips keep mechanical prompts off `main` inventory until Promote

## Setup

1. Copy workflows into your app repo (or submodule this folder).
2. Add GitHub Actions secrets:
   - `OHM_API_KEY` — Ohm Bearer key (`sk-at-…`)
   - `OHM_API_URL` — default `https://api.withohm.dev` (optional override)
3. Point your suite at Ohm with the tip header (see `scripts/chat-once.sh`).
4. Create/select the Neon branch with your usual Neon Action/CLI — we do not reimplement Neon here.

## Workflows

| File | When | What |
|------|------|------|
| `.github/workflows/ohm-preview.yml` | `pull_request` | Ensure tip `pr-N` exists; run a smoke chat with `X-Ohm-Cache-Tree` |
| `.github/workflows/ohm-promote-on-merge.yml` | `push` to default branch after merge | `POST /v1/cache/trees/pr-N/promote` |

## Manual curls

```bash
export OHM_API_URL=https://api.withohm.dev
export OHM_API_KEY=sk-at-YOUR_KEY
export OHM_TIP=pr-842

# Fork tip from main (idempotent if you already created it)
curl -sS -X POST "$OHM_API_URL/v1/cache/trees" \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$OHM_TIP\"}"

# Chat on the tip
curl -sS "$OHM_API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: $OHM_TIP" \
  -d '{"model":"mock","messages":[{"role":"user","content":"ping"}]}'

# On merge — Promote inventory into main
curl -sS -X POST "$OHM_API_URL/v1/cache/trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Docs

- https://www.withohm.dev/docs/compose-neon
- https://www.withohm.dev/docs/cache-trees
- https://www.withohm.dev/product/architecture
