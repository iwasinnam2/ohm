# Partner JSON research (personalization only)

Use withOhm JSON fetch to brief yourself on **public** company/product/careers pages before outreach.  
**Not** for building email lists — Ohm blocks lead harvest / cold-email purposes; PII redaction strips emails.

See [LEGAL.md](../LEGAL.md) and `src/at_utility/compliance/policy.py`.

---

## Allowed purposes

| Purpose | Use on |
|---------|--------|
| `public_company_info` | About / company pages |
| `business_catalog` | Public product pages |
| `job_listings` | Careers (agent/LLM/Cursor signals) |
| `public_web_retrieval` | Public docs / eng blogs |

---

## Workflow

1. Put candidate `research_urls` in [partner_hit_list.csv](partner_hit_list.csv).
2. Run the script (or MCP / curl below).
3. From `title` / `text` / `json_ld`, write `personalization_hook` + refine `pain_observed`.
4. Find `person` on a channel they already use — not from scraped mailto links.
5. Send the design-partner message from [PARTNER_HIT_LIST.md](PARTNER_HIT_LIST.md).

---

## Script

```powershell
# Research assist — requires OHM_API_KEY (your seat, not a harvest key)
.\scripts\partner_research_fetch.ps1 `
  -Urls "https://example.com/about","https://example.com/careers" `
  -Purpose public_company_info
```

Writes a short brief to stdout and optionally `-OutFile briefs\<slug>.json`.

---

## MCP

In Cursor with withOhm attached:

```text
ohm_fetch_web(
  urls=["https://example.com/about"],
  format="json",
  purpose="public_company_info"
)
```

---

## curl (production path — same as MCP / research script)

Public API does not expose raw `/v1/ingest`; use chat + web context with `web_format: json` (tenant terms already bound at Checkout/admin mint):

```bash
curl -s https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"mock",
    "messages":[{"role":"user","content":"Extract what they build and any agent/LLM/Cursor signals."}],
    "fetch_web_context":true,
    "web_format":"json",
    "web_purpose":"public_company_info",
    "web_urls":["https://example.com/about"],
    "cache_control":"no_store"
  }'
```

---

## What to extract into the CSV

- What they build (one clause)
- Agent / LLM / Cursor / browse signals
- Hiring language that proves agent workload
- **Never** store harvested personal emails from page text

---

## Done when

- [ ] Script runs against api.withohm.dev with your key
- [ ] At least a few hit-list rows have `personalization_hook` filled from JSON briefs
