# Neon — withOhm utilisation (incl. Backup & Restore)

Project: **`REDIS REPLICA DIST HUBS`** (`cold-band-78080621`), region
**`aws-us-east-2`**. Prod API/Redis live in **us-east-1** — every mirror write
is a cross-region hop until the project is recreated in us-east-1 or left as
a cold audit store.

## Role in withOhm today

| System | Role |
|--------|------|
| **ElastiCache Redis** | Hot path + real-time source of truth (tenants, keys, cache, meters) |
| **Neon Postgres** | Optional durable **mirror** when `OHM_DB_ENABLED=true` + `DATABASE_URL` |
| **Stripe** | Money truth |

Mirror tables (`accounts`, `usage_daily`, `billing_events`) are coded in
`src/at_utility/db/` but **not applied** on this Neon project yet — only
`neon_auth.*` tables exist. `OHM_DB_ENABLED` defaults **false**. So Neon is
provisioned ahead of the mirror going live.

## Assessment of Neon Backup & Restore / Snapshots

What the page gives you:

| Capability | Free plan | Paid (Launch/Scale) | withOhm fit |
|------------|-----------|---------------------|-------------|
| Instant restore (PITR / history window) | **6 hours** (capped) | up to 7d / 30d; history storage **$0.20/GB-mo** | Useful once mirror holds billing audit |
| Manual snapshots | **1** | 100; storage **$0.09/GB-mo** (full charge) | Pre-migration safety once schema is live |
| Scheduled backup snapshots | **No** | Yes (not on Agent plan); first full then incremental | Daily/weekly once `billing_events` matter for SOC2 |
| Restore to point / snapshot | Yes | Yes | Ops recovery for mirror; does **not** replace Redis snapshots |

### Verdict for withOhm

**Not useful as a cost lever today.** The DB is ~32 MB and has no ohm mirror
tables. Paying for scheduled snapshots or a long history window now buys
almost nothing.

**Useful later**, when the mirror is on:

1. **Before risky schema/reconciler changes** — take **1 manual snapshot**
   (Free allows one; enough pre-revenue).
2. **After revenue / SOC2 evidence** — Launch plan + **daily scheduled
   snapshots** with short retention (7–14d) for `billing_events` audit
   durability. Snapshots at $0.09/GB-mo are cheaper than maxing the history
   window at $0.20/GB-mo for the same retention story — keep history at **1 day**
   for instant oops-recovery, rely on snapshots for week-scale restore.
3. **Does not replace Redis backups.** Tenant keys and cache still need
   ElastiCache snapshots (`redis_snapshot_retention_days`). Neon restore
   cannot rebuild Redis.

## History window / Instant restore

Console: **Settings → Instant restore**. API field today:
`history_retention_seconds: 21600` (**6 hours** — Free plan max).

Neon keeps WAL change history for that window. Instant restore, Time Travel,
branching from past states, and snapshots all rely on it. WAL outside the
window is dropped and stops counting toward **History** on the bill.

| Plan | Default | Maximum | History cost |
|------|---------|---------|--------------|
| Free | 6 hours | 6 hours (capped at 1 GB) | **No charge** |
| Launch | 1 day | 7 days | **$0.20/GB-month** |
| Scale | 1 day | 30 days | **$0.20/GB-month** |

History is **separate** from branch **Storage** (logical data size). Setting
the window to **0** minimizes History usage but **disables** Instant restore
and Time Travel — on Free that saves **$0** and only removes capability.

withOhm mapping: Instant restore / Time Travel / branch-from-past only cover
the **Postgres mirror**. They do not roll back Redis tenants, keys, or cache.

### Locked phase table

| Phase | History window | Why |
|-------|----------------|-----|
| **Now (Free, mirror idle)** | **Keep 6 hours** (already set) | Free max; History $0; keep oops-restore. Do **not** set to 0. Do **not** upgrade just for 7d. |
| **Mirror on, still Free** | Stay at **6 hours** | Still no History charge; take the **1** manual snapshot before schema/reconciler risk |
| **Launch + mirror live** | **1 day** (Launch default), not 7 | Instant oops-recovery; week-scale via scheduled snapshots |
| **SOC2 / ≥90d audit** | Snapshots + export — history alone cannot do 90d (Scale max is 30d) | See `docs/SOC2_ROADMAP.md` |

Split of duties:

| Lever | Job | Cost signal |
|-------|-----|-------------|
| **History window** | Short oops window (hours→1 day) | Free: $0; paid: $0.20/GB-mo WAL |
| **Snapshots** | Week-scale / pre-migration / SOC2 retention | $0.09/GB-mo; schedules need paid |

Neon’s “production → 7 days” guidance assumes Launch/Scale and real write
traffic. Wrong buy while the mirror is empty — maxing history is more
expensive than **1d history + scheduled snapshots** for the same story.

### What to do on Neon **now** (slim, no architecture change)

1. **Scale-to-zero** — project `default_endpoint_settings.suspend_timeout_seconds`
   is **`0` (always on)**. Set suspend to **300s** (5 min) in Neon Console →
   Compute. Idle mirror traffic does not justify always-on CU. **This** is the
   Neon cost win, not the history slider.
2. **Leave history at 6h** (Free max; confirm Settings → Instant restore).
   Do not set to 0; do not buy Launch just for a longer window.
3. **Do not enable snapshot schedules** until `accounts` / `billing_events`
   are populated.
4. Optional: recreate the project in **`aws-us-east-1`** when you turn the
   mirror on for real — cuts latency and a confusion tax. Not urgent while
   `OHM_DB_ENABLED=false`.

### When mirror goes live (checklist)

```text
[ ] Apply src/at_utility/db/schema.sql to the Neon branch
[ ] Set OHM_DB_ENABLED=true + DATABASE_URL on the gateway (Secrets)
[ ] Manual snapshot once schema is green
[ ] Reconciler --apply verified writing accounts + usage_daily
[ ] Webhook path appending billing_events
[ ] (Launch) History window = 1 day — not 7; never rely on history for SOC2 90d
[ ] (Paid) Schedule daily snapshots, retention 7–14d
[ ] Document restore drill: snapshot → new branch → validate → reset/cutover
```

SOC2 roadmap wants audit/ledger ≥90d (`docs/SOC2_ROADMAP.md`) — that is a
**paid Neon + scheduled snapshots** (or export) problem later, not a Free-plan
6h history problem and not solvable by maxing the history window (30d Scale
cap).

## Related

- Mirror package: `src/at_utility/db/`
- Redis SoT backups: `infra/terraform/main.tf` (`redis_snapshot_*`)
- Cost slim (AWS): [COST_FREEZE.md](COST_FREEZE.md)
