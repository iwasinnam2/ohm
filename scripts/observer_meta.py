#!/usr/bin/env python3
"""Observer meta — Observer watches Observer (stdlib only).

Daily check: for every scheduled Observer workflow, confirm a recent
*successful* run exists within a cadence window sized for GitHub Actions
schedule jitter (not the nominal cron). Purpose: catch paused schedules,
broken workflows, and dead credentials — not page when */15 pulse merely
arrives 2–3h late, which is normal on GitHub-hosted runners.

Env: GITHUB_TOKEN, GITHUB_REPOSITORY (provided by the workflow), plus the
observer_notify sink env.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

from observer_notify import notify

# workflow file -> max age (hours) for the last *successful* run.
# GitHub Actions schedule delay is large for high-frequency crons (*/15 often
# stretches to 2–3h gaps in practice). Windows must absorb that jitter and
# still catch "schedule paused for days" — the failure mode this script exists
# for. Tight windows that page on healthy delayed pulses defeat the Observer.
EXPECTED = {
    "observer-pulse.yml": 6,  # cron */15; GitHub often delivers every 2–3h
    "golden-path.yml": 30,  # nightly
    "pricing-pulse.yml": 8 * 24,
    "observer-admin.yml": 33 * 24,
}


def last_successful_run(repo: str, token: str, workflow: str) -> dict | None:
    """Most recent completed run with conclusion=success (skip cancelled/failed)."""
    url = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}"
        "/runs?status=completed&per_page=20"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        data = json.loads(res.read().decode("utf-8"))
    for run in data.get("workflow_runs") or []:
        if run.get("conclusion") == "success":
            return run
    return None


def last_completed_run(repo: str, token: str, workflow: str) -> dict | None:
    url = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}"
        "/runs?status=completed&per_page=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        data = json.loads(res.read().decode("utf-8"))
    runs = data.get("workflow_runs") or []
    return runs[0] if runs else None


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        print("observer-meta: GITHUB_TOKEN/GITHUB_REPOSITORY missing", file=sys.stderr)
        return 1

    now = time.time()
    problems: list[str] = []
    for workflow, max_age_hours in EXPECTED.items():
        try:
            latest = last_completed_run(repo, token, workflow)
            run = last_successful_run(repo, token, workflow)
        except Exception as exc:  # noqa: BLE001 — an unqueryable workflow is a finding
            problems.append(f"{workflow}: API query failed ({exc})")
            continue
        if run is None:
            if latest is None:
                problems.append(f"{workflow}: no completed runs found")
            else:
                problems.append(
                    f"{workflow}: no successful run in last 20 completed "
                    f"(latest conclusion={latest.get('conclusion')})"
                )
            continue
        started = run.get("run_started_at") or run.get("created_at") or ""
        try:
            started_dt = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            age_hours = (now - started_dt.timestamp()) / 3600
        except ValueError:
            age_hours = -1.0
        line = (
            f"{workflow}: last success {age_hours:.1f}h ago "
            f"({run.get('html_url')})"
        )
        if latest and latest.get("id") != run.get("id"):
            line += f"; latest completed={latest.get('conclusion')}"
        print(line)
        if 0 <= max_age_hours < age_hours:
            problems.append(
                f"{workflow}: last success {age_hours:.1f}h ago "
                f"(expected within {max_age_hours}h — schedule may be paused)"
            )

    if not problems:
        print("observer-meta: all Observer workflows healthy")
        return 0
    body = "\n".join(f"- {p}" for p in problems) + (
        "\n\nIf schedules were paused by repo inactivity, re-enable them under "
        "Actions -> select workflow -> Enable."
    )
    print(f"observer-meta: {len(problems)} problem(s)\n{body}", file=sys.stderr)
    notify(f"heartbeat: {len(problems)} Observer workflow(s) unhealthy", body)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
