# Quickstart

Point any OpenAI-compatible client at one base URL. Keep your keys (BYOK).
Connect MCP hosts from the [integrations board](/docs/integrations) when you
want agents in the loop.

## Paths

1. **Seat:** [/billing/intermediate](/billing/intermediate) — Checkout issues your withOhm key.
2. **Try without an IDE:** [/workbench](/workbench) Agent Shell, or [/demo](/demo) for the 60s miss→HIT proof.
3. **SDK base URL:** `https://api.withohm.dev/v1` (local edge: `http://localhost:8081/v1`).
4. **BYOK:** send your provider key as `X-Ohm-Upstream-Key`. Authorization stays `sk-at-…`.
5. **Govern:** [/org](/org) — cost centers, ledger statement, policy.
6. **Connect tools:** [Integrations](/docs/integrations) — Cursor, Claude Code, VS Code, Windsurf, Zed.
7. **Enterprise:** [/billing/enterprise](/billing/enterprise).

## Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-at-YOUR_OHM_KEY",
    base_url="https://api.withohm.dev/v1",
    default_headers={"X-Ohm-Upstream-Key": "sk-proj-..."},  # BYOK on miss
)
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "hi"}],
)
```

Identical second call → Redis cache hit (`x-at-cache: HIT`).

## curl

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer sk-at-YOUR_OHM_KEY" \
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"ohm-self-proof-v1"}]}'
```

Self-proof runbook: [docs/SELF_PROOF.md](https://github.com/iwasinnam2/ohm/blob/master/docs/SELF_PROOF.md) (source is open).
