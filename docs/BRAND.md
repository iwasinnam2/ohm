# Name and promise

**Product name:** Ohm

**Logo:** Ohm symbol (Ω) — Greek capital omega as the sole mark on the first screen. App / marketplace icon: [`brand/ohm-icon-360.png`](../brand/ohm-icon-360.png) (360×360). Vector source: [`brand/ohm-icon.svg`](../brand/ohm-icon.svg).

## Cursor distribution

| Path | What it is | Agreement? |
|------|------------|------------|
| **Deeplink** (`cursor://…/mcp/install`) | One-click MCP install into the user’s Cursor | None — works today from `/billing/success` |
| **cursor.directory** | Community listing | Usually free submit / listing norms |
| **Cursor Marketplace plugin** | Official Customize → Plugins / MCP browse | Open-source plugin + **manual Cursor review** via [marketplace publish](https://cursor.com/marketplace/publish) — not an Adobe-style commercial partnership |
| **Native “built into Cursor”** | First-party product placement | Separate BD / partnership with Cursor (Adobe-class) — out of band |

Ship deeplink first; package a `.cursor-plugin` with MCP + icon for marketplace submission when ready.

Launch GTM (from zero partners): [LAUNCH_GTM.md](LAUNCH_GTM.md).  
Contextual Cursor install chips: [CURSOR_DISCOVERY.md](CURSOR_DISCOVERY.md).  
Site on Amplify: [AMPLIFY_SITE.md](../infra/runbooks/AMPLIFY_SITE.md).

**Promise (one sentence):**

> Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.

**Category language:** AI traffic utility / model ingress — not “wrapper.”

**Visual:** one logo mark (Ω), one color system on docs, site, and error pages. No feature laundry list on the first screen.

## What we sell (voice)

Lead with **latency/cache relief** and **compliant web context**. The bill is trust and pipe rent — not managed-token wholesale theatre. See [VISION.md](VISION.md).

## Hosts (owned)

Root **`withohm.dev`** is registered (GoDaddy .dev + domain protection + Microsoft 365 email).

| Role | Host |
|------|------|
| Marketing / docs | `https://withohm.dev` / `www` (apex cutover when ready) |
| Public API | `https://api.withohm.dev` (ACM issued; edge cutover separate) |
| Status (future) | `https://status.withohm.dev` |
| Partner email | `partners@withohm.dev` |

Until AWS edge cutover, the supported chat contract remains local `http://localhost:8081/v1`. Docs may temporarily share the `api.*` hostname on Vercel — disclosed on-site.

## Internal vs public names

| Public | Internal (deferred rename) |
|--------|----------------------------|
| Ohm | Python package `at_utility`, k8s/Terraform `at-utility` |
| Customer keys | Prefix remains `sk-at-*` until a dedicated key-prefix cutover |
| Response headers | `X-AT-*` until rename |
| Upstream BYOK header | `X-Ohm-Upstream-Key` |

## Distribution

1. OpenAI-compatible API — change `base_url` + Ohm key; pass provider key via `X-Ohm-Upstream-Key` (BYOK).
2. Cursor / MCP attach — see [CURSOR.md](CURSOR.md).
3. Thin SDK helpers under `sdks/` may publish later as `@ohm/sdk` / `ohm-sdk`; until then package paths stay `@at-utility/sdk` / `at-utility-sdk`.

## Legal (MVP)

Public: Terms, Privacy, DPA, Security, Compliance on the site `/docs/*`. Repo templates: [`docs/legal/`](legal/). API acks bind `tos-2026-07-26` / `dpa-2026-07-26`.
