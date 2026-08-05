# Automations

Operator notes for the scheduled Cursor automations. Nothing here is part of any
prompt — each automation's prompt is a whole file on its own, so it can be selected
and pasted without trimming.

| Automation | Prompt file | Cadence |
| --- | --- | --- |
| Daily upkeep and community listening | [`DAILY_1800.md`](DAILY_1800.md) | Daily, 18:00 |

Findings land in [`UPKEEP_LOG.md`](UPKEEP_LOG.md), and the mechanical half of the
daily run lives in [`scripts/daily_upkeep.py`](../../scripts/daily_upkeep.py). Change
the script to change *what* is checked; change the prompt to change *how the agent
reasons* about the results.

## The daily 18:00 automation

Three jobs, one pass, every evening:

1. Run the **Observer meta chain by hand** rather than trusting the 06:45 UTC
   schedule. `observer-meta.yml` failed 3 of 5 scheduled runs in early August 2026 on
   schedule jitter alone, so a second read on a different clock is worth having.
2. **Upkeep** of the withOhm production surfaces and the repo around them, read-only
   from outside, because `docs/OPERATIONS.md` keeps Terraform, secrets, DNS, and
   Stripe as human-credentialed actions and the agent VM holds no AWS credentials.
3. **Read one Hacker News or Y Combinator post** and draft a reply responding to the
   post and nothing else. Draft only — the automation never posts.

## Configuring the trigger

Automations are server-side objects at [cursor.com/automations](https://cursor.com/automations);
there is no repo file format for them, which is why the prompt is kept here and pasted
in. Four things to get right:

**Schedule.** Pick a preset or enter a cron expression. Cron runs in UTC, so `0 18 * * *`
is 18:00 UTC. For a local 6pm year-round, prefix the timezone: `CRON_TZ=Europe/London 0 18 * * *`.

**Repository.** Set it explicitly to `iwasinnam2/ohm`. For schedule and Slack triggers
Cursor defaults to *no repository*, and a no-repo run never clones the code, so every
step in the prompt would fail on a missing `/workspace` and it could not open a PR.

**Prompt.** Paste the whole of `DAILY_1800.md`. Do not add a heading, a wrapper, or
`---` delimiters around it.

**Tools.** MCP servers are attached per automation and are not inherited from your
normal cloud agent setup. See the table below.

## Which MCP connectors to attach

| Connector | Verdict | What it buys the daily run |
| --- | --- | --- |
| Linear | Attach | Finds stale open `[observer]` issues, which silently disable alerts. The highest-value connector here. |
| Stripe | Attach, read-only | Open disputes have hard evidence deadlines nothing else watches; also past-due invoices and price/meter drift. |
| Neon | Attached, use read-only | Little to do yet — see below. Becomes slow queries, error logs, and schema drift once the mirror is live. |
| Cursor Cloud | Built in | Watches the automation itself: failed prior runs and a rotting environment build. |
| AWS Knowledge | Optional | Confirms lifecycle and end-of-support dates instead of trusting hardcoded ones. |
| AWS Pricing | Optional | The region-posture decision in `docs/OPERATIONS.md` is cost-gated, but that is a monthly question, not a daily one. |
| Vercel, Cloudflare, Amplitude, Hex | Skip | withOhm runs on AWS — EKS, Amplify, CloudFront. These have no surface in this product, and every attached tool is more context and more ways to go wrong. |

**Neon is in write mode**, so destructive tools such as `delete_branch`,
`delete_project`, and `prepare_database_migration` are exposed to the agent. Those
tools instruct the caller to ask the user first, and an unattended 18:00 run has
nobody to ask. The prompt forbids them explicitly, but a read-only Neon connection is
the stronger control if you can scope one — belt and braces on an unattended job that
can reach production data.

The connector currently holds one project, `REDIS REPLICA DIST HUBS`
(`cold-band-78080621`), created 2026-07-30 with `cpu_used_sec: 0` and no compute
activity since the day it was made. That is expected while the Postgres mirror in PRs
#8 and #9 is unmerged, and it is why the prompt tells the agent to keep the nightly
Neon check to a single line rather than waking an idle compute. Two things about it
are worth a decision before it holds anything real: it sits in `aws-us-east-2` while
production is deliberately single-region in `us-east-1`, and its IP allowlist is empty
with `block_public_connections: false`, so it accepts connections from anywhere.

## Why the prompt file has no preamble

The prompt is the entire file, deliberately. An earlier draft opened with explanatory
notes and separated them from the body with a `---` horizontal rule, which is a bad
shape for something meant to be copied: selecting from the rule inclusive yields a
prompt beginning with `---` and no closing delimiter, the exact form of an
unterminated YAML frontmatter block. Anything that parses frontmatter — and Cursor
does parse it in `SKILL.md` and `.mdc` files — can choke on that. The operator notes
therefore live here instead.

## If a run misbehaves

**"Failed to read schedule".** The schedule lives on the trigger, not in the prompt,
so this points at the trigger record. In order: check
[status.cursor.com](https://status.cursor.com), since Automations incidents look like
configuration errors. Then repaste the prompt from a clean copy of `DAILY_1800.md`,
which now contains no `---` at all. If it survives both, delete the automation and
recreate it with the schedule and prompt both set *before* the first save — Cursor
support has repeatedly given recreate-from-scratch as the fix for schedule edits that
do not take effect server-side, and editing a schedule after creation is the known
trigger for it.

**The run starts but every command fails.** Almost certainly no repository is
attached; see the trigger notes above.

**The run is green but nothing lands in the repo.** That is intended. Green nights
leave no trace, and the run history is the heartbeat.
