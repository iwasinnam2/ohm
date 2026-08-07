Branch exact-replay inventory for PRs and agents — fork, promote, freeze without cloning a database.

A tip is a named address in inventory. Clients select it with `X-Ohm-Cache-Tree`. Default tip is `main`. Ephemeral tips (`pr-842`, `agent-a`) keep work off `main` until Promote.

For pairing inventory tips with a database preview branch in CI, see [Compose with Neon](/docs/compose-neon).
