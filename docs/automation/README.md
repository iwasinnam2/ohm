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
step in the prompt would fail and it could not open a PR.

Note that `ohm` is the repository *name*, not a filesystem path — the checkout lands
at `/workspace`, not `/ohm`. The prompt does not depend on either: it opens with
`cd "$(git rev-parse --show-toplevel)"`, which lands at the repository root wherever
the environment happens to put it, including a multi-repo layout where each repo gets
its own subdirectory.

**Prompt.** Paste the whole of `DAILY_1800.md`. Do not add a heading, a wrapper, or
`---` delimiters around it.

**Tools.** MCP servers are attached per automation and are not inherited from your
normal cloud agent setup. See the table below.

## Which MCP connectors to attach

| Connector | Verdict | What it buys the daily run |
| --- | --- | --- |
| Linear | Attach | Finds stale open `[observer]` issues, which silently disable alerts. The highest-value connector here. |
| Stripe | Attach, read-only | Open disputes have hard evidence deadlines nothing else watches; also past-due invoices and price/meter drift. |
| Neon | Attach read-only | Slow queries, error logs, mirror schema drift, and dev branches left running and billing. |
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

Two things about the `REDIS REPLICA DIST HUBS` project (`cold-band-78080621`) want
closing before it holds tenant or billing data. Its IP allowlist is empty with
`block_public_connections: false`, so it accepts connections from anywhere with a
valid password — set `allowed_ips` to the cluster egress addresses, or turn on
`block_public_connections` and reach it over a VPC endpoint. And it sits in
`aws-us-east-2` while production is deliberately single-region in `us-east-1`, which
puts a cross-region hop on every mirror write.

## Secrets

Three secrets are read by the daily run. They live in Cursor Dashboard → Cloud Agents
→ Secrets, are injected as environment variables into the agent VM, and are never
committed. The prompt forbids echoing any of them, because the report and PR body the
run produces are far more visible than the environment they came from.

Give each one its own credential rather than reusing an existing key. A per-consumer
credential can be revoked on its own, and when something does leak, the value tells
you which consumer leaked it.

### `OHM_ADMIN_KEY`

Unlike the other two, this is not issued by a provider — you mint it yourself. There
is no signature, no derivation, and no required format: `Settings.is_admin_api_key`
in `src/at_utility/config.py` does a plain set-membership test against the
comma-separated `AT_ADMIN_API_KEYS` environment variable. A key is "valid" precisely
because it appears in that list on the cluster, which means minting one is three
steps — generate a strong random string, register it, roll the pods that read it.

**It is not a read-only credential, and that is the part worth pausing on.** The same
`admin_dep` dependency in `src/at_utility/main.py` gates four endpoints: `/v1/admin/ops`,
which is all the sweep needs, plus tenant minting, tenant status changes, and checkout
creation. A key handed to an unattended nightly job can therefore create tenants.
Because the variable is a list, mint a *dedicated* key and append it rather than
reusing an existing one — revocation then stays surgical and an incident stays
attributable.

Use [`scripts/issue_admin_key.ps1`](../../scripts/issue_admin_key.ps1), which does the
whole sequence with the same no-history discipline as `rotate_stripe_key.ps1`:

```powershell
powershell -File scripts/issue_admin_key.ps1
```

It reads the current list, generates a 256-bit key, appends it, rolls
`deploy/gateway`, polls `/v1/admin/ops` until the key is accepted, and prints the
value exactly once at the end for pasting into Cursor Secrets. To take one out of
circulation:

```powershell
powershell -File scripts/issue_admin_key.ps1 -Revoke
```

which prompts for the key at a hidden prompt, removes just that entry, rolls, and
confirms the key now gets a 403.

Four details it handles that are easy to get wrong by hand:

**The fallback trap.** `admin_api_key_set` resolves
`self.at_admin_api_keys or self.at_api_keys`, so while `AT_ADMIN_API_KEYS` is empty
every `AT_API_KEYS` value is admin-capable by fallback. Patching a lone new key into
that field silently revokes all of them the moment the pods roll. The script detects
the empty field, warns, and seeds the list with the fallback values so nothing loses
access.

**Never emptying the list.** An empty `AT_ADMIN_API_KEYS` hands admin rights back to
every tenant key at once, so the script refuses to write one and refuses to revoke
the last remaining key.

**Which deployment to roll.** Only the Python control plane pulls the whole secret
through `envFrom`, and it is the one serving the admin endpoints. `gateway-rs` takes
named keys and is unaffected.

**Verifying before you trust it.** A `403` after the rollout almost always means an
unpatched secret or an un-rolled pod rather than a bad key, so the script polls
rather than assuming, and fails loudly if the key never becomes valid.

Afterwards, run `python3 scripts/daily_upkeep.py` and confirm section 2 shows an
`admin ops` line instead of a `SKIP` — that is the same code path the automation
takes, so it is end-to-end proof rather than a proxy for it.

The stronger fix, if you want it later, is a separate read-only ops key set checked
by a new dependency on `/v1/admin/ops` alone, so the observability path cannot mint
anything. Until then, the dedicated-key approach limits blast radius.

### `LINEAR_API_KEY` and `LINEAR_TEAM_ID`

In Linear, go to Settings → Security & access → Personal API keys → New API key. Name
it for the consumer, for example `withohm-observer`, so it is obvious in the list and
obvious in an audit. The key is shown once; copy it straight into Cursor Secrets.

Scope it as narrowly as Linear allows — the observer only needs to read issues and
create them. Prefer a workspace-level application or a service account over your own
personal key if your plan offers one, since a personal key carries your full access
and dies with your account.

`LINEAR_TEAM_ID` is the UUID the new issues are filed against. Read it from the API
rather than guessing:

```bash
curl -s https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" -H 'Content-Type: application/json' \
  -d '{"query":"{ teams { nodes { id key name } } }"}'
```

The team ID is not a secret and can be stored as plain configuration; only the key
needs protecting. Rotation is delete-then-create in the same settings page.

### `SLACK_WEBHOOK_URL`

Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps) → From
scratch, pick the workspace, then Incoming Webhooks → Activate → Add New Webhook to
Workspace, and choose the single channel alerts should land in.

**The URL is itself the credential.** Anyone holding it can post to that channel as
the app, with no further authentication, so treat it exactly like a password: never
in a commit, an issue, a screenshot, or a log line. Its blast radius is confined to
posting in one channel, which is why a webhook is preferable here to a bot token with
broader scopes.

Point it at a dedicated alerts channel rather than a channel people converse in, so
noise is separable and the audience is deliberate. Rotate by deleting the webhook in
the app's Incoming Webhooks page and adding a new one; the old URL dies immediately.

### Rotating anything

Revoke first, then re-issue, then update Cursor Secrets, then run
`python3 scripts/daily_upkeep.py` once by hand to confirm the affected section comes
back green. If a value is ever exposed, revoking it is always cheaper than reasoning
about whether anyone saw it.

## Why the prompt survives being pasted as plaintext

The automation prompt box strips markdown: backticks, code fences, and bullet markers
all disappear, and lists collapse into blank-line-separated paragraphs. That is fine —
the model reads the content the same either way, and every command in the prompt sits
on its own line, so losing the fences never joins two commands together.

Two consequences shaped how the prompt is written. It contains **no markdown links**,
because a link's target is dropped on paste and only its text survives. And **every
path is relative to the repository root**, not to this directory, because the prompt
executes from `/workspace`. An earlier draft used `../../scripts/observer_notify.py`
and a bare `UPKEEP_LOG.md`, which are correct for a file living in `docs/automation/`
and wrong for a prompt: the first is a dead path from the root, and the second would
have had the agent create a new log at the repo root every night instead of appending
to the real one.

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
