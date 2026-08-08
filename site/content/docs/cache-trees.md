# Cache trees

Exact-replay inventory can be scoped per preview or agent run — without
branching a database.

Default traffic uses the `main` tree (unchanged cache keys). Set
`X-Ohm-Cache-Tree` (or body `cache_tree`) to isolate HITs for a PR or run.
Fork, promote, freeze, and reset are available on `/v1/cache/trees`.

<!-- ohm:cache-trees-flowchart -->

Tips isolate exact-replay inventory per PR or agent run. For pairing tips with
a database preview branch in CI, see [Compose with Neon](/docs/compose-neon).
Full design note: [docs/CACHE_TREES.md](https://github.com/iwasinnam2/ohm/blob/master/docs/CACHE_TREES.md) (source is open).

## Select a tree

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "X-Ohm-Cache-Tree: pr-842" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'
```

Invalid names return `400`. Frozen trees reject new writes (`409`) but can
still serve HITs.

COW reads may serve a parent blob without copying into the child tip. That is
not yet a single shared content-addressed store with many refs — Promote still
copies child-local digests. See [docs/CACHE_TREES.md](https://github.com/iwasinnam2/ohm/blob/master/docs/CACHE_TREES.md) ("Storage honesty" section).

## Fork, promote, freeze

```bash
# Fork from main
curl -s https://api.withohm.dev/v1/cache/trees \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"pr-842"}'

# After warming the preview tree, merge new digests into main
curl -s https://api.withohm.dev/v1/cache/trees/pr-842/promote \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'

# Freeze a finished CI artifact
curl -s https://api.withohm.dev/v1/cache/trees/pr-842/freeze \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -X POST
```

Promote copies digests written on the child into the parent index (COW reads
mean the child could already HIT parent warm entries without copying).
