"""Daily upkeep sweep — one deterministic pass over Observer, production, repo (stdlib only).

Written for the 18:00 daily automation (docs/automation/DAILY_1800.md). The
agent runs this once and reasons about the report; everything mechanical lives
here so the sweep is reviewable code rather than prose re-improvised each
evening.

Deliberately read-only. It probes, queries, and reports — no deploys, no
Terraform, no kubectl, no Stripe writes. Those stay human-credentialed by
design (docs/OPERATIONS.md "Remaining intentional local/operator actions").

Sections:
  1. Observer meta chain — are the scheduled Observer workflows still alive?
  2. Observer pulse      — are the live customer surfaces up right now?
  3. TLS expiry          — nothing else watches this; Route53 checks liveness only.
  4. CI on master        — failed runs in the last 24h.
  5. Deadlines           — dated obligations approaching (EKS support, etc).
  6. Public stats        — business heartbeat from /v1/public/stats.
  7. Observer backlog    — open [observer] Linear issues that blind title dedup.

Env (all optional — every section degrades to a SKIP rather than a crash):
  GITHUB_TOKEN       falls back to `gh auth token`; needs only actions:read
  GITHUB_REPOSITORY  falls back to the origin remote
  OHM_ADMIN_KEY      enables the /v1/admin/ops billing-pipeline probe
  LINEAR_API_KEY     enables the Observer backlog section
  plus the observer_notify sink env when --notify is passed.

Exit code is the worst severity found: 0 green, 1 amber, 2 red.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import redirect_stdout
from datetime import datetime, timezone

import observer_meta
import observer_pulse
from observer_notify import notify

GREEN, AMBER, RED = 0, 1, 2
LABEL = {GREEN: "green", AMBER: "amber", RED: "red"}

API = "https://api.withohm.dev"
TLS_HOSTS = ("api.withohm.dev", "www.withohm.dev")
TLS_AMBER_DAYS = 30
TLS_RED_DAYS = 14

# Dated obligations that no alarm will ever fire for. Add a row when a
# commitment gains a date; delete it once the work has shipped.
DEADLINES: list[tuple[str, str]] = [
    (
        "2026-11-26",
        "EKS 1.31 extended support ends — the cluster must be on a newer "
        "Kubernetes by this date (PR #10 bumps to 1.36)",
    ),
]
DEADLINE_WARN_DAYS = 120

# An open [observer] issue suppresses the next alert with the same title,
# because observer_notify dedups on exact title. Stale ones are alert-blinding.
LINEAR_GQL = "https://api.linear.app/graphql"
BACKLOG_STALE_DAYS = 3


class Report:
    """Accumulates markdown sections plus the findings that set the severity."""

    def __init__(self) -> None:
        self.sections: list[str] = []
        self.findings: list[tuple[int, str]] = []

    def add(self, title: str, body: str) -> None:
        self.sections.append(f"## {title}\n\n{body.rstrip()}\n")

    def finding(self, severity: int, text: str) -> None:
        self.findings.append((severity, text))

    @property
    def severity(self) -> int:
        return max((s for s, _ in self.findings), default=GREEN)

    def render(self, *, repo: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        head = [f"# Daily upkeep — {stamp}", "", f"Repository: `{repo}`", ""]
        if self.findings:
            head.append(f"**Status: {LABEL[self.severity]}** — actionable items:")
            head.append("")
            for severity, text in sorted(self.findings, key=lambda f: -f[0]):
                head.append(f"- `{LABEL[severity]}` {text}")
        else:
            head.append("**Status: green** — nothing actionable.")
        head.append("")
        return "\n".join(head) + "\n" + "\n".join(self.sections)


def _get(url: str, headers: dict[str, str] | None = None, timeout: int = 20):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:500]
    except Exception as exc:  # noqa: BLE001 — an unreachable endpoint is a finding
        return 0, f"{type(exc).__name__}: {exc}"


def resolve_repo() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repo:
        return repo
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""
    url = url.removesuffix(".git")
    if "://" not in url:  # scp-style: git@github.com:owner/repo
        return url.split(":")[-1].strip("/")
    # urlsplit keeps any embedded credential out of .path, so the slug — which
    # is printed in the report — can never carry a token.
    return urllib.parse.urlsplit(url).path.strip("/")


def resolve_token() -> str:
    """Prefer an explicit token; otherwise borrow the gh CLI's (actions:read is enough)."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    try:
        return subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def section_observer_meta(report: Report, repo: str, token: str) -> None:
    """Reuse observer_meta's own windows so this never drifts from the workflow."""
    if not repo or not token:
        report.add("1. Observer meta chain", "SKIP — no GitHub token or repository.")
        report.finding(AMBER, "Observer meta chain unverified: no GitHub token.")
        return

    now = time.time()
    lines: list[str] = []
    for workflow, max_age_hours in observer_meta.EXPECTED.items():
        try:
            latest = observer_meta.last_completed_run(repo, token, workflow)
            run = observer_meta.last_successful_run(repo, token, workflow)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"- `{workflow}` — query failed: {exc}")
            report.finding(AMBER, f"{workflow}: Actions API query failed.")
            continue
        if run is None:
            detail = (
                f"latest conclusion={latest.get('conclusion')}"
                if latest
                else "no completed runs"
            )
            lines.append(f"- `{workflow}` — no successful run in last 20 ({detail})")
            report.finding(RED, f"{workflow}: no recent successful run ({detail}).")
            continue
        started = run.get("run_started_at") or run.get("created_at") or ""
        try:
            age = (
                now
                - datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ) / 3600
        except ValueError:
            age = -1.0
        trailing = ""
        if latest and latest.get("id") != run.get("id"):
            trailing = f", latest completed run was `{latest.get('conclusion')}`"
        stale = 0 <= max_age_hours < age
        mark = "STALE" if stale else "ok"
        lines.append(
            f"- `{workflow}` — {mark}: last success {age:.1f}h ago "
            f"(window {max_age_hours}h){trailing}"
        )
        if stale:
            report.finding(
                AMBER,
                f"{workflow}: last success {age:.1f}h ago, past its {max_age_hours}h "
                "window — the schedule may be paused, which is not the same as "
                "production being down.",
            )
        elif trailing:
            report.finding(
                AMBER,
                f"{workflow}: a green run is still inside the window but the most "
                f"recent run concluded `{latest.get('conclusion')}`.",
            )
    report.add("1. Observer meta chain", "\n".join(lines))


def section_pulse(report: Report) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        failures = observer_pulse.run_probes()
    probe_log = buffer.getvalue().strip()
    body = "```\n" + probe_log + "\n```"
    if failures:
        body += "\n\nFailures:\n" + "\n".join(f"- {f}" for f in failures)
        for failure in failures:
            report.finding(RED, f"Live probe red — {failure}")
    report.add("2. Observer pulse (live surfaces)", body)


def section_tls(report: Report) -> None:
    lines: list[str] = []
    context = ssl.create_default_context()
    for host in TLS_HOSTS:
        try:
            with socket.create_connection((host, 443), timeout=15) as raw:
                with context.wrap_socket(raw, server_hostname=host) as tls:
                    cert = tls.getpeercert()
            expires = datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=timezone.utc)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"- `{host}` — check failed: {exc}")
            report.finding(AMBER, f"TLS expiry unknown for {host}: {exc}")
            continue
        days = (expires - datetime.now(timezone.utc)).days
        issuer = dict(x[0] for x in cert.get("issuer", ())).get("organizationName", "?")
        lines.append(
            f"- `{host}` — {days} days left (expires {expires:%Y-%m-%d}, issuer {issuer})"
        )
        if days <= TLS_RED_DAYS:
            report.finding(RED, f"TLS certificate for {host} expires in {days} days.")
        elif days <= TLS_AMBER_DAYS:
            report.finding(AMBER, f"TLS certificate for {host} expires in {days} days.")
    report.add("3. TLS expiry", "\n".join(lines))


def section_ci(report: Report, repo: str, token: str) -> None:
    if not repo or not token:
        report.add("4. CI on master (24h)", "SKIP — no GitHub token or repository.")
        return
    url = (
        f"https://api.github.com/repos/{repo}/actions/runs"
        "?branch=master&status=failure&per_page=30"
    )
    status, raw = _get(
        url,
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if status != 200:
        report.add("4. CI on master (24h)", f"Query failed (HTTP {status}).")
        report.finding(AMBER, "Could not list failed CI runs on master.")
        return
    cutoff = time.time() - 24 * 3600
    recent = []
    for run in json.loads(raw).get("workflow_runs") or []:
        try:
            started = (
                datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        except (KeyError, ValueError):
            continue
        if started >= cutoff:
            recent.append(run)
    if not recent:
        report.add("4. CI on master (24h)", "No failed runs on `master` in the last 24h.")
        return
    lines = [
        f"- `{run.get('name')}` — {run.get('created_at')} ({run.get('html_url')})"
        for run in recent
    ]
    report.add("4. CI on master (24h)", "\n".join(lines))
    names = sorted({str(run.get("name")) for run in recent})
    report.finding(
        AMBER,
        f"{len(recent)} failed run(s) on master in the last 24h: {', '.join(names)}.",
    )


def section_deadlines(report: Report) -> None:
    if not DEADLINES:
        report.add("5. Deadlines", "None tracked.")
        return
    today = datetime.now(timezone.utc).date()
    lines: list[str] = []
    for iso, description in sorted(DEADLINES):
        try:
            due = datetime.strptime(iso, "%Y-%m-%d").date()
        except ValueError:
            continue
        days = (due - today).days
        lines.append(f"- **{iso}** ({days} days) — {description}")
        if days < 0:
            report.finding(RED, f"Deadline passed {abs(days)} days ago: {description}")
        elif days <= DEADLINE_WARN_DAYS:
            report.finding(AMBER, f"{days} days until {iso}: {description}")
    report.add("5. Deadlines", "\n".join(lines))


def section_public_stats(report: Report) -> None:
    status, raw = _get(f"{API}/v1/public/stats")
    if status != 200:
        report.add("6. Public stats", f"Unavailable (HTTP {status}).")
        return
    try:
        data = json.loads(raw)
    except ValueError:
        report.add("6. Public stats", "Non-JSON response.")
        return
    keys = (
        "cache_hit_tokens",
        "estimated_provider_avoided_usd",
        "estimated_pipe_proxy_avoided_usd",
        "receipts_minted",
    )
    lines = [f"- `{k}`: {data[k]}" for k in keys if k in data]
    lines.append("")
    lines.append(
        "Estimates only (`estimate_only: true`) — provider-list estimate, not a "
        "guaranteed savings figure. See docs/GEM_POSITION.md."
    )
    report.add("6. Public stats", "\n".join(lines))


def section_observer_backlog(report: Report) -> None:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not key:
        report.add(
            "7. Observer backlog (Linear)",
            "SKIP — `LINEAR_API_KEY` unset.\n\n"
            "While this is unset the sweep cannot see whether a stale open "
            "`[observer]` issue is suppressing new alerts: observer_notify dedups "
            "on exact title, so an unresolved issue silently swallows the next "
            "identical page.",
        )
        return
    query = {
        "query": (
            "query { issues(first: 50, filter: {"
            '  title: { startsWith: "[observer]" },'
            '  state: { type: { nin: ["completed", "canceled"] } }'
            "}) { nodes { identifier title url createdAt } } }"
        )
    }
    req = urllib.request.Request(
        LINEAR_GQL,
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            data = json.loads(res.read().decode("utf-8"))
        nodes = (((data or {}).get("data") or {}).get("issues") or {}).get("nodes") or []
    except Exception as exc:  # noqa: BLE001
        report.add("7. Observer backlog (Linear)", f"Query failed: {exc}")
        report.finding(AMBER, f"Could not read the Observer Linear backlog: {exc}")
        return
    if not nodes:
        report.add("7. Observer backlog (Linear)", "No open `[observer]` issues.")
        return
    now = datetime.now(timezone.utc)
    lines: list[str] = []
    for issue in nodes:
        created = str(issue.get("createdAt", ""))
        try:
            age = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).days
        except ValueError:
            age = -1
        lines.append(
            f"- {issue.get('identifier')} ({age}d) — {issue.get('title')} "
            f"({issue.get('url')})"
        )
        if age >= BACKLOG_STALE_DAYS:
            report.finding(
                AMBER,
                f"{issue.get('identifier')} has been open {age} days and is blinding "
                f"title dedup for: {issue.get('title')}",
            )
    report.add("7. Observer backlog (Linear)", "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily withOhm upkeep sweep")
    parser.add_argument(
        "--notify",
        action="store_true",
        help="fan findings out through observer_notify (Slack + Linear)",
    )
    parser.add_argument(
        "--skip-pulse",
        action="store_true",
        help="skip the live production probes",
    )
    args = parser.parse_args()

    repo = resolve_repo()
    token = resolve_token()
    report = Report()

    section_observer_meta(report, repo, token)
    if args.skip_pulse:
        report.add("2. Observer pulse (live surfaces)", "SKIP — --skip-pulse.")
    else:
        section_pulse(report)
    section_tls(report)
    section_ci(report, repo, token)
    section_deadlines(report)
    section_public_stats(report)
    section_observer_backlog(report)

    print(report.render(repo=repo or "unknown"))

    severity = report.severity
    if args.notify and severity > GREEN:
        body = "\n".join(
            f"- {LABEL[s]}: {t}" for s, t in sorted(report.findings, key=lambda f: -f[0])
        )
        notify(f"daily upkeep: {LABEL[severity]}", body)
    return severity


if __name__ == "__main__":
    raise SystemExit(main())
