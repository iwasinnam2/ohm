#!/usr/bin/env python3
"""Observer meta — Observer watches Observer (stdlib only).

Daily self-consistency check: for every scheduled Observer workflow, query the
GitHub API for the most recent completed run and verify it (a) happened within
its expected cadence window and (b) concluded successfully. A watchdog that
silently stops running is worse than no watchdog — this catches disabled
schedules (GitHub pauses crons on 60 days of repo inactivity), broken
workflows, and revoked credentials.

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

# workflow file -> max age (hours) for the last completed run. Windows are
# ~2x cadence so a single slow/queued run doesn't page.
EXPECTED = {
    "observer-pulse.yml": 2,
    "golden-path.yml": 30,
    "pricing-pulse.yml": 8 * 24,
    "observer-admin.yml": 33 * 24,
}


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
            run = last_completed_run(repo, token, workflow)
        except Exception as exc:  # noqa: BLE001 — an unqueryable workflow is a finding
            problems.append(f"{workflow}: API query failed ({exc})")
            continue
        if run is None:
            problems.append(f"{workflow}: no completed runs found")
            continue
        conclusion = run.get("conclusion")
        started = run.get("run_started_at") or run.get("created_at") or ""
        try:
            started_dt = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            age_hours = (now - started_dt.timestamp()) / 3600
        except ValueError:
            age_hours = -1.0
        line = (
            f"{workflow}: last run {conclusion}, "
            f"{age_hours:.1f}h ago ({run.get('html_url')})"
        )
        print(line)
        if conclusion != "success":
            problems.append(f"{workflow}: last completed run was {conclusion}")
        elif 0 <= max_age_hours < age_hours:
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
