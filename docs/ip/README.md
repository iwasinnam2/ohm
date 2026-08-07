# withOhm — UK IPO attorney briefing pack (Phase A)

Internal pack for a **claimability consult** (not a filing instruction).
Not legal advice. Do not treat this folder as a patent specification.

## Legal frame (locked July 2026)

- *Emotional Perception AI Ltd* **[2026] UKSC 3** — *Aerotel* overruled; UK aligns with EPO **G1/19**
- **UKIPO Practice Note 14 July 2026** — any hardware → **intermediate technical-character filter** → Pozzoli novelty/inventive step on surviving features only
- Battleground is **intermediate-step stripping** (metering/pipe rent out), not a classic s.1(2) Aerotel refusal

## Binary threshold

| Path | When |
|------|------|
| **Do not file** broad “caching IAAS” | Always — filtered / obvious vs commodity caches |
| **File narrow UK (or EP) application** | Only if counsel marks FSM / trees / receipts **Green** (or Amber with gap-close) for **technical character** through the intermediate filter **and** inventive step |
| **Defensive publication + trade secrets** | If all candidates Red / Amber-without-path |

## Pack contents

| File | Purpose |
|------|---------|
| **[BRIEF.md](BRIEF.md)** | **Single submission attachment** — legal frame, A/B/C, gaps, prior art, Traffic Light, fee cap |
| [05-EMAIL-TEMPLATE.md](05-EMAIL-TEMPLATE.md) | Outreach body (attach BRIEF.md only) |
| [01-ATTORNEY-SHORTLIST.md](01-ATTORNEY-SHORTLIST.md) | Firm list + asks (internal; not required as attachment) |
| [00-BRIEF.md](00-BRIEF.md) | Pointer to BRIEF.md |
| [02-PRIOR-ART.md](02-PRIOR-ART.md) · [03-GAP-AUDIT.md](03-GAP-AUDIT.md) · [04-DISCLOSURE-INVENTORY.md](04-DISCLOSURE-INVENTORY.md) | Source detail now folded into BRIEF.md; keep for internal expansion |
| [GAP-CLOSE-AND-LOOSE-ENDS.md](GAP-CLOSE-AND-LOOSE-ENDS.md) | Full gap inventory, dual-use build tranches, conversation loose ends |

## Code anchors

- Edge HIT gate: `gateway-rs/src/main.rs` (`edge_hit_gate`, HIT path)
- Control-plane admit: `src/at_utility/main.py` → `POST /internal/edge-hit`
- Receipts: `src/at_utility/receipts.py`, `docs/RECEIPTS.md`
- Cache trees: `src/at_utility/cache_trees.py`, `docs/CACHE_TREES.md`
- Architecture / non-goals: `docs/ARCHITECTURE.md`, `GET /v1/public/honesty`

## Phase status

- **A (this pack):** ready to send — fee-capped Traffic Light consults
- **B:** attorney binary opinion (file / do not file)
- **C-1 / C-2:** file narrow claims **or** freeze defensive publication
