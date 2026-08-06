# Signed cache-hit receipts

Every cache HIT can carry a **signed receipt** — a detached proof of what the
pipe did, verifiable by anyone against a public key. This is the fourth
pillar ("replay and audit value") as an artifact instead of a sentence: don't
trust the savings copy, verify the receipt.

## What a receipt is

A compact JWS (EdDSA / Ed25519) in the `X-Ohm-Receipt` response header of
every served cache hit — JSON and streamed-replay hits from the Python plane,
and edge-served hits from the Rust plane (minted by the control plane during
the `/internal/edge-hit` gate, so the edge never holds the signing key).

Payload fields:

| Field | Meaning |
|-------|---------|
| `v`, `kind` | Schema version, `cache_hit` |
| `iat`, `region`, `plane` | When and where the hit was served (`python` / `rust-edge`) |
| `model` | Requested model id |
| `tokens_replayed` | Upstream tokens that were **not** re-bought |
| `pipe_usd` | What Ohm billed for the hit (the meter event, 6 dp) |
| `request_sha256` | The exact-replay identity — digest of the canonicalized request |
| `tenant_sha256` | Truncated tenant fingerprint (self-verifiable, not identifying) |

## Verify one from a cold start

```bash
# 1. Capture a receipt (identical request twice; second one is the HIT)
curl -si https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"receipt demo"}]}' \
  | grep -i x-ohm-receipt

# 2. Verify it against the public key directory — no Ohm code required
python scripts/verify_receipt.py "<X-Ohm-Receipt value>" --base https://api.withohm.dev
```

The verifier fetches `/.well-known/http-message-signatures-directory`,
resolves the key by the JWS `kid` (RFC 7638 JWK thumbprint), and checks the
Ed25519 signature. A forged or altered receipt fails; so does a receipt
signed by a key that is not in the published directory.

## Operator setup

| Env | Meaning |
|-----|---------|
| `AT_RECEIPT_ED25519_SEED_B64` | base64(url) 32-byte seed. Empty → receipts disabled, responses unchanged |

Generate: `python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`

The receipt key is deliberately **distinct** from the Web Bot Auth key
(`AT_WEB_BOT_AUTH_ED25519_SEED_B64`) so either can rotate independently; both
public keys are served from the same well-known directory. Set the seed on
the Python gateway only — the Rust edge receives minted receipts through the
edge-hit gate response and never holds key material.

## Why this exists

Post-LLM, prose is free and therefore trustless. Receipts move the core
claim — *exact-replay hits that cost zero upstream tokens* — from marketing
into cryptography: the meter event and the replay identity are signed at the
moment of service, and the customer's auditor can replay the verification
without believing anyone. See also `GET /v1/public/honesty` for the full
list of published limits and the surfaces that prove them.
