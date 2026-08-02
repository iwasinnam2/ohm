# Self-proof runbook (miss → HIT → receipt)

Generate live hit-ratio evidence yourself. Prompts must be **byte-identical**
(no timestamps, no random suffixes).

## A — Agent Shell (preferred product surface)

1. Open https://www.withohm.dev/demo (or `/workbench`).
2. Paste your Intermediate key (`sk-at-…`).
3. Leave model `mock` (no BYOK needed for pipe proof).
4. Click **Run miss→HIT demo**.
5. Confirm strip: first `MISS`, second `HIT`; ledger event count / pipe rent ticks.
6. Screenshot the meta strip + demo highlight.

## B — Cursor MCP (compatibility path)

Exact prompts:

```text
ohm_chat(prompt="ohm-self-proof-v1", model="mock")
ohm_chat(prompt="ohm-self-proof-v1", model="mock")
ohm_savings()
ohm_receipt(display_name="withOhm self-proof")
```

Expect: first chat cache miss, second hit; savings shows hits; receipt returns a
public badge URL.

## C — SDK / curl

```bash
export OHM_KEY=sk-at-YOUR_KEY
BODY='{"model":"mock","messages":[{"role":"user","content":"ohm-self-proof-v1"}]}'

curl -sD - https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" | head -n 20

curl -sD - https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" | head -n 20
```

Look for `x-at-cache: MISS` then `x-at-cache: HIT`.

Mint receipt (if your build exposes it):

```bash
curl -s https://api.withohm.dev/v1/receipts \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"withOhm self-proof"}'
```

## What to publish

- Public receipt / badge URL on README and directory listing.
- Optional: screenshot of Shell demo strip.

## Discipline

- Same model string, same message content, same role order.
- Do not append dates, UUIDs, or “retry 2” to the proof prompt.
- `mock` proves the pipe; swap a real model + BYOK when you want provider-path proof.
