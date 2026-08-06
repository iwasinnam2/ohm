# Signed cache-hit receipts

Every cache HIT can carry `X-Ohm-Receipt` — an Ed25519 JWS you can verify against the public JWKS directory.

## Verify

```bash
curl -si https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"receipt demo"}]}' \
  | grep -i x-ohm-receipt
```

Fetch keys from `/.well-known/http-message-signatures-directory`. Repository verifier: `scripts/verify_receipt.py`.

## Payload (selected fields)

| Field | Meaning |
|-------|---------|
| `tokens_replayed` | Upstream tokens not re-bought |
| `pipe_usd` | What Ohm metered for the hit |
| `request_sha256` | Exact-replay identity |
| `plane` / `region` | Where the HIT was served |
| `tree_id` / `tree_name` | Optional cache-tree claims |

## Related

[Trust docs](/docs/trust) · [Honesty](/docs/honesty) · [Product: Trust](/product/trust)
