Run agent fleets through a single OpenAI-compatible base URL. Keep BYOK. Turn identical tool loops and retries into zero-upstream-token HITs — with receipts you can show finance.

## Summary

- **One contract** — Shell, MCP, SDK, Cursor: same `/v1/chat/completions` shape.
- **Zero-token replay** — Exact matches HIT Redis; labs are not re-billed for the completion.
- **Tree isolation** — Give each agent or session class a cache tree when shared `main` is too coarse.
- **Governed browse** — Compliant public-web fetch on the pipeline side, not shadow scrapers.
- **Ledger** — Path tags and org export for FinOps.

## Why agents need a pipe (not another model)

Agents multiply **identical** work: retries, evaluator loops, CI prompt packs. Bigger context windows do not remove that waste. withOhm is the tollbooth on repeated inference — not a competing lab.

## Anti-pattern: every agent talks to labs bare

- No HIT inventory → every retry pays prefill again
- No org ledger → shadow AI spend
- No shared inventory hygiene → preview pollution on `main`

## How withOhm wins

1. Point the agent runtime at `api.withohm.dev/v1` with BYOK headers.
2. Tag `X-Ohm-Path` for cost centers; optional `X-Ohm-Cache-Tree` per fleet.
3. Read `/v1/usage` and signed receipts on HITs.

## Trust fence

Replay inventory is never a training corpus. Prove the loop: [Waste demo](/product/waste-demo).

## Next

[Product: Pipe](/product/pipe) · [Quickstart](/docs/quickstart) · [Cursor / MCP](/docs/cursor) · [Start — $0 seat](/billing/intermediate)
