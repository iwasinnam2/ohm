# Angel pitch + proof pack (draft) — withOhm

**Status:** Draft for operator-angel chats. Fills the 1-pager gap called out in
[INVESTOR_INTRO_TARGETS.md](INVESTOR_INTRO_TARGETS.md). Aligned to the PR #40–45 climate
(IP posture, Intermediate seats, billing-grade HIT FSM/receipts, admit fencing File-lean,
investor doctrine, brand polish).

**Honesty:** No invented ARR, logos, or “interested investors.” Patent filing is parallel
counsel work — not the pitch lead.

**Named warm leads:** [WARM_LEAD_LISTS.md](WARM_LEAD_LISTS.md)

---

## 1. One-liner

**withOhm is a metered exact-match replay pipe** (OpenAI-compatible ingress) between apps
and LLM providers — rent the plumbing, keep your keys, govern the chaos. Not a model
reseller. Not a semantic cache.

Canonical wedge: [GEM_POSITION.md](../GEM_POSITION.md)

---

## 2. Why now (PR #40–45 climate)

| Signal | What shipped | Investor translation |
|--------|--------------|----------------------|
| **#41** Intermediate email/password seats + product surface | Accounts restore bearer without paste; waste demo path | Self-serve pipe rent is real |
| **#42** Dual-use Tranche 1 | HIT FSM (`LOOKUP→…→RELEASE`), digest-scoped meter IDs, richer receipts, tree-bleed honesty | Billing-grade cache, not best-effort middleware |
| **#43** File-lean admit fencing | HMAC admit token + Redis lease (flags off); defensive-pub checklist | Race-safe edge HIT path ready for counsel File path |
| **#40** IP pack | Copyright / invention disclosure / trademark posture under MIT dual model | Entity can assign IP into Ltd without re-licensing OSS away |
| **#44** Investor intro doctrine | Design partners → operator angels → UK/EU seed | Raise sequence is disciplined |
| **#45** Brand rails | Site polish | Public face matches “utility / pipe” tone |

Live: https://www.withohm.dev · API: https://api.withohm.dev · MIT: https://github.com/iwasinnam2/ohm

---

## 3. Problem → wedge → who pays

**Problem.** Agent products re-pay identical prefill/completions on retries, self-consistency
loops, and CI prompt suites. Provider prefix cache and routing proxies (LiteLLM-class) do
different jobs — see [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md).

**Wedge.** Exact-match Redis inventory + HIT/MISS meters + signed receipts + compliant web
fetch. Labs stay labs (BYOK). Ohm bills **pipe rent**.

**Who pays.** Intermediate: $0 membership + meters. Enterprise: contact / commit. Design
partners: complimentary time-boxed seat for quote + usage proof.

**Dual ledger** (`/v1/savings`): `estimated_provider_avoided_usd` vs `pipe_rent_usd` +
`roi_ratio` — always `estimate_only: true`. Never promise guaranteed savings SLAs.

---

## 4. Architecture (say this in 60 seconds)

```text
Client → Rust edge (:8081)
           │  Redis GET (exact digest)
           ├─ HIT  → Pipeline meters + optional X-Ohm-Receipt → body
           └─ MISS → Python control plane (:8080) → BYOK upstream → SET → meter MISS
```

- **Ephemeral Side:** exact-replay trees / blobs / edge locality  
- **Pipeline:** Stripe, receipts, SSO, FinOps, admit fencing  
- **Cache trees:** COW namespaces (`main`, `pr-N`) compose with Neon branches  

Honesty: production edge HITs go live when ElastiCache secrets flip; until then edge may
full-proxy — correctness OK ([SIEGE_DEFENSE.md](SIEGE_DEFENSE.md), OPERATIONS).

---

## 5. Proof pack (non-negotiable before intros)

1. Live product URL + Intermediate or design-partner key path  
2. `/v1/usage` paste or screenshot (hits, misses, pipe USD) + optional `X-Ohm-Receipt`  
3. One public design-partner sentence **or** waste-check demo (https://www.withohm.dev/demo)  
4. This one-pager (or PDF export)  
5. Entity plan: sole trader OK for first operator-angel chats; **Ltd + IP assignment** before
   institutional seed; SEIS/EIS once Ltd (accountant confirms — don’t promise)

---

## 6. Ask variants

### List A — operator angel

> Raising a small UK seed once Ltd exists. Looking for an operator angel who has built
> gateways / edge / Redis / observability / AI platform — cheque + advice on pipe-rent GTM.
> SAFE/ASA informal OK with counsel until Ltd.

### List B — design peer / partner

> 90-day complimentary `design_partner` seat (BYOK). In exchange: one public sentence +
> `/v1/usage` snapshot after a week. No deck required.
> Apply: https://www.withohm.dev/design-partners · partners@withohm.dev

### Neon / Cursor shaped BD (not a raise)

- Neon: compose exact-replay tips with AI Gateway — [NEON_BD_BRIEF.md](NEON_BD_BRIEF.md)
  (**Bryan Clark WAITING — do not capital-ping**)  
- Cursor: pilot after ≥3 receipt-backed quotes — [CURSOR_BD_BRIEF.md](CURSOR_BD_BRIEF.md)

---

## 7. Forwardable intro blurb

> [Name] built withOhm — OpenAI-compatible **exact-match** replay pipe (not semantic cache).
> Design partners / Intermediate seats see HIT-ratio + pipe rent on `/v1/usage` with signed
> receipts. Billing-grade HIT FSM + admit fencing in-repo; IP packet ready for Ltd
> assignment. Raising a small UK seed once Ltd is in place. Worth a 20-min look?
> Live: https://www.withohm.dev — one-pager + meter snapshot attached.

---

## 8. Siege answers (keep short)

| Attack | One-line |
|--------|----------|
| Exact-match never hits | Agents retry/loop/CI — mechanical repeats; prove on their `/v1/savings` |
| Billing me for not working | Replay is the work; ~$2/M HIT vs full provider; dual ledger |
| LiteLLM / Helicone / Portkey | Routing vs billing-grade exact replay + compliance fetch — different jobs |
| Provider prompt cache | Prefix discount ≠ full response replay; not cross-provider |
| MITM keys | BYOK header per request, never persisted; hits need no upstream key |

Full text: [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md)

---

## 9. Entity / raise sequence

```text
Sole trader + live pipe
  → design partners + meter proof
  → operator angel chats (SAFE/ASA + counsel)
  → Ltd + IP assignment + SEIS/EIS setup
  → Episode 1 / Seedcamp-class seed
  → patent File decision in parallel (counsel Traffic Lights) — not the pitch lead
```

Patent counsel last on the capital funnel ([INVESTOR_INTRO_TARGETS.md](INVESTOR_INTRO_TARGETS.md)).

---

## 10. Weekly rhythm (unchanged)

1. Mon — update 3 real CSV people ([investor_intro_targets.csv](investor_intro_targets.csv))  
2. Tue–Thu — design-partner touches  
3. Fri — one fund/angel deep-dive  
4. Never — mass-email patent firms or “intro agencies”

---

## 11. One-page PDF export checklist

When exporting for an introducer, keep to one page:

1. One-liner + non-goals (no semantic cache / no token wholesale)  
2. Architecture sketch (edge HIT / control-plane MISS)  
3. Dual-ledger screenshot  
4. Ask + entity timeline  
5. Links: product, API docs, GitHub, this pack URL in-repo  

Do not lead with patent claims or Neon/Cursor logo asks.
