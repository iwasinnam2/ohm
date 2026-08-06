# Upkeep log

Trail of the daily 18:00 automation ([`DAILY_1800.md`](DAILY_1800.md)). Newest
entry first; the automation trims this to the most recent 30.

Only nights that produced something actionable are recorded here. Green nights
leave no entry on purpose — the Cursor run history and the GitHub Actions history
are the heartbeat, and a daily "all fine" commit would train people to stop reading
this file. An entry therefore always means something wanted attention.

Format: one heading per night, the sweep's status, the findings that earned the
entry, and what was done or handed off.

<!-- newest entry goes directly below this line -->

## 2026-08-05 — amber (first run)

Trial run of the automation, executed by hand to validate the instruction body.

- **Observer meta chain** — all four watched workflows inside their windows:
  pulse 0.7h/6h, golden-path 12.8h/30h, pricing-pulse 56.1h/192h, admin
  104.9h/792h. Live probes all green. `/v1/admin/ops` unverified, `OHM_ADMIN_KEY`
  unset.
- **CI red on master** — `Observer meta` failed 09:22 UTC. Triaged as the old 2h
  window false-paging on schedule jitter (`last success 2.1h ago (expected within
  2h)`), already fixed by `8e0332d` widening the window to 6h. No action.
- **Alert path is blinded** — that same run logged `open Linear issue already
  exists for: [observer] heartbeat: 1 Observer workflow(s) unhealthy`. Because
  `observer_notify` dedups on exact title, the next genuine heartbeat page will be
  swallowed until that issue is closed. Handed off: needs a human in Linear, and
  `LINEAR_API_KEY` set so section 7 can see it.
- **EKS 1.31 extended support ends in 113 days** (2026-11-26). PR #10 bumps to
  1.36 and has sat untouched since 2026-07-30.
- **3 high-severity npm advisories** under `site/node_modules/sharp`. Not auto-fixed;
  `npm audit fix --force` is a major bump.
- TLS healthy — api 186 days, www 190 days. Stale-PR check clean at the 14-day
  threshold; #5–#12 are 6 days old.
- **Hacker News** — read item 49182041, "TIME Is Serving AI Bots a Different
  Website, with Ads Built In". Draft written, not posted. The linked article was
  read through the ingest pipe as the nightly self-test: `ok: true`,
  `metered_fetches: 1`, `robots: "checked"`, `pii_redactions: 0`.
