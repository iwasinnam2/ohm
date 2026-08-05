# OhmBot verification + signing seeds (operator runbook)

Two related operations: (A) set the Ed25519 signing seeds in production, and
(B) register OhmBot in Cloudflare's Verified Bots program via Web Bot Auth.
Do (A) first — (B) verifies against the key directory that (A) makes live.

## Production rollout order (trust architecture / PR #12)

Images ship via GitHub Actions **Deploy API** on push to `master` (OIDC → ECR
→ `kubectl set image`). No local Docker/ECR from the laptop. Secrets still
need one operator `kubectl patch` (the deploy role cannot write secrets).

1. **Merge** PR #12 into `master` (includes `gateway-rs` public passthrough for
   `/.well-known/http-message-signatures-directory` — without that, GA/NLB
   returns 401 on the JWKS directory).
2. **Watch** Actions → *Deploy API* until green (`/health` check at the end).
3. **Set seeds** (section A below) and `rollout restart` gateway (+ ingest-worker
   if enabling OhmBot). Restart is required so pods pick up the new secret keys.
4. **Verify**:
   ```bash
   curl -s https://api.withohm.dev/v1/public/honesty | python -m json.tool
   # expect receipts.enabled true once AT_RECEIPT_ED25519_SEED_B64 is set
   curl -si https://api.withohm.dev/.well-known/http-message-signatures-directory | head -12
   # expect 200 + Signature / Signature-Input (not 401)
   # HIT twice with the same body, then:
   python scripts/verify_receipt.py "<X-Ohm-Receipt>" --base https://api.withohm.dev
   ```
5. **Optional:** Cloudflare Verified Bots form (section B).

## A. Set the signing seeds

Two independent seeds (never reuse one for both — they rotate separately):

| Env | Signs | Lives on |
|-----|-------|----------|
| `AT_WEB_BOT_AUTH_ED25519_SEED_B64` | OhmBot's outbound fetches (RFC 9421, `tag="web-bot-auth"`) | ingest-worker + gateway (gateway serves the public key) |
| `AT_RECEIPT_ED25519_SEED_B64` | `X-Ohm-Receipt` cache-hit receipts (`docs/RECEIPTS.md`) | gateway only |

Generate (run twice, one per seed — treat output as a live secret, never
commit or paste into a PR/log):

```powershell
python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

Production (EKS, same pattern as `SINGLE_REGION.md`; the gateway `envFrom`s
`at-utility-secrets`, the ingest worker reads the bot seed via `secretKeyRef`):

```powershell
# base64-wrap each value for the k8s secret data field
$wrap = { param($s) [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($s)) }
kubectl --context ohm-us-east-1 -n at-utility patch secret at-utility-secrets --type merge `
  -p ('{"data":{"AT_RECEIPT_ED25519_SEED_B64":"' + (& $wrap $receiptSeed) + '"}}')
kubectl --context ohm-us-east-1 -n at-utility patch secret at-utility-secrets --type merge `
  -p ('{"data":{"AT_WEB_BOT_AUTH_ED25519_SEED_B64":"' + (& $wrap $botSeed) + '"}}')
kubectl --context ohm-us-east-1 -n at-utility rollout restart deploy/gateway deploy/ingest-worker
```

Local dev: put both seeds in `.env` (see `.env.example`) and
`docker compose up -d --force-recreate gateway ingest-worker`.

Verify after rollout:

```bash
curl -si https://api.withohm.dev/.well-known/http-message-signatures-directory | head -8
# expect: 200, content-type application/http-message-signatures-directory+json,
# Signature-Input/Signature headers (directory self-binding), keys[] JWKS body
curl -s https://api.withohm.dev/v1/public/honesty | grep -o '"enabled": *[a-z]*'
# then mint + verify a receipt end to end:
#   send an identical chat body twice, grab X-Ohm-Receipt from the HIT,
#   python scripts/verify_receipt.py "<receipt>" --base https://api.withohm.dev
```

Note: requires the image containing `at_utility.receipts` +
`compliance/web_bot_auth` (PR #12). Setting the secrets earlier is harmless —
the envs are inert until the code arrives.

## B. Register OhmBot as a Cloudflare Verified Bot

Prerequisites (all shipped once A is done):

- Key directory at `https://api.withohm.dev/.well-known/http-message-signatures-directory`
  serving the JWKS with the required content type **and self-signed response**
  (one binding per key, `tag="http-message-signatures-directory"` — Cloudflare
  refuses unsigned directories so nobody can register a mirrored JWKS).
- OhmBot sends `Signature`, `Signature-Input` (components include
  `signature-agent`, `tag="web-bot-auth"`), and `Signature-Agent:
  "https://api.withohm.dev/.well-known/http-message-signatures-directory"`
  on every fetch (`AT_WEB_BOT_AUTH_SIGNATURE_AGENT` in the prod configmap).
- Stable UA (`OhmBot/0.1 (+https://www.withohm.dev/docs/legal; …)`), public
  policy page (`/docs/legal`), robots.txt honored fail-closed, 402/403
  honored — all per Cloudflare's verified bots policy.

Submission (Cloudflare dashboard):

1. Log in → account home → **⋯** next to the account name → **Configurations**
   → **Bot Submission Form** (a.k.a. Verified Bots tab).
2. Bot type: **Verified Bot** (not Signed Agent — a bot cannot be both;
   OhmBot is a fetcher/crawler, not an on-behalf-of-user browsing agent).
3. Verification Method: **Request Signature**.
4. Validation Instructions: `https://api.withohm.dev/.well-known/http-message-signatures-directory`.
5. User-Agent values: `OhmBot/0.1 (+https://www.withohm.dev/docs/legal; public-retrieval; respect-robots)`;
   match pattern: `OhmBot`.
6. Category/purpose: AI inference / retrieval (fetch-time context, **not**
   training — consistent with `/v1/compliance/policy`).
7. Submit; keep `partners@withohm.dev` reachable for the review thread.

After approval OhmBot appears in Cloudflare Radar's bot directory; origins
that allow verified bots stop challenging it, and pay-per-crawl 402 flows
carry a verifiable identity (Ohm still never auto-pays —
`pay_per_crawl: surface_402_no_autopay`).

Rotation: generate a new seed, add the new public key by deploying with both
seeds temporarily (directory serves both), flip the active seed, remove the
old one after cached directory TTLs (1h) expire.
