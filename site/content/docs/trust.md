# Trust — verify it yourself

Prose is cheap. Every load-bearing claim withOhm makes ships with the surface
that checks it, so nothing here has to be taken on faith.

## Signed cache-hit receipts

Every cache HIT carries an `X-Ohm-Receipt` response header: a compact JWS
(EdDSA/Ed25519) signed at the moment of service, stating the replay identity
(`request_sha256`), the upstream tokens that were **not** re-bought
(`tokens_replayed`), and what the hit was billed (`pipe_usd`).

```bash
# Same body twice — the second response is the HIT and carries the receipt
curl -si https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"receipt demo"}]}' \
  | grep -i x-ohm-receipt
```

Verify it with nothing but the public key directory — no withOhm code:

```bash
python scripts/verify_receipt.py "<X-Ohm-Receipt value>" --base https://api.withohm.dev
```

The verifier resolves the signing key by its RFC 7638 thumbprint from
`/.well-known/http-message-signatures-directory` and checks the Ed25519
signature. Forged or altered receipts fail. Edge-served hits carry the same
receipt — minted by the control plane, so the edge never holds key material.

## Published limits — the honesty endpoint

```bash
curl -s https://api.withohm.dev/v1/public/honesty
```

Machine-readable list of what the pipe will **not** do — no mid-stream
handoff after the first byte, no semantic cache, no auto-paying HTTP 402
pay-per-crawl, no robots evasion, no cache-as-training-corpus — each entry
paired with the endpoint that proves or enforces it. If an entry there stops
being true, that is an incident, not a copy edit.

## Verified crawler identity

OhmBot signs its web fetches with RFC 9421 HTTP Message Signatures
(`tag="web-bot-auth"`); origins verify against the same public directory.
Fetch refusals (402 licensed-crawl, robots, 401/403 revocations) are honored
and surfaced, never worked around.

## Track record

- Nightly [golden-path workflow](https://github.com/iwasinnam2/ohm/actions/workflows/golden-path.yml)
  walks the reviewer path against production — the history is public.
- The gateway is MIT-licensed and open: [github.com/iwasinnam2/ohm](https://github.com/iwasinnam2/ohm).
- Cross-tenant savings counter at `/v1/public/stats` is always labeled
  `estimate_only: true`.
