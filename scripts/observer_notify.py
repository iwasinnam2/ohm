"""Observer notification fan-out: Slack webhook + Linear issue (stdlib only).

Used by the Observer workflows (observer-pulse, observer-meta, observer-admin,
pricing-pulse, golden-path). Missing credentials degrade gracefully: each sink
is skipped with a notice so a probe never fails just because a secret is
absent.

Env:
  SLACK_WEBHOOK_URL   Slack incoming webhook (optional)
  LINEAR_API_KEY      Linear personal/OAuth API key (optional)
  LINEAR_TEAM_ID      Linear team UUID for created issues (optional)

CLI:
  python scripts/observer_notify.py --title "[observer] api down" \
      --body "details..." [--slack-only | --linear-only]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

LINEAR_GQL = "https://api.linear.app/graphql"
OBSERVER_PREFIX = "[observer]"


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read().decode("utf-8")
    try:
        return json.loads(raw)
    except ValueError:
        return {"raw": raw}


def notify_slack(text: str) -> bool:
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        print("observer_notify: SLACK_WEBHOOK_URL unset — skipping Slack")
        return False
    _post_json(url, {"text": text}, {})
    print("observer_notify: Slack posted")
    return True


def _linear_headers() -> dict[str, str] | None:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not key:
        print("observer_notify: LINEAR_API_KEY unset — skipping Linear")
        return None
    return {"Authorization": key}


def linear_open_observer_issue_exists(title: str) -> bool:
    """Dedup: an open issue with the same title means the incident is known."""
    headers = _linear_headers()
    if headers is None:
        return False
    query = {
        "query": (
            "query($t: String!) { issues(first: 50, filter: {"
            "  title: { eq: $t },"
            '  state: { type: { nin: ["completed", "canceled"] } }'
            "}) { nodes { id title } } }"
        ),
        "variables": {"t": title},
    }
    try:
        data = _post_json(LINEAR_GQL, query, headers)
        nodes = (((data or {}).get("data") or {}).get("issues") or {}).get(
            "nodes"
        ) or []
        return len(nodes) > 0
    except Exception as exc:  # noqa: BLE001 — dedup failure must not block paging
        print(f"observer_notify: Linear dedup query failed ({exc}); creating anyway")
        return False


def notify_linear(title: str, body: str) -> bool:
    headers = _linear_headers()
    if headers is None:
        return False
    team = os.environ.get("LINEAR_TEAM_ID", "").strip()
    if not team:
        print("observer_notify: LINEAR_TEAM_ID unset — skipping Linear")
        return False
    if linear_open_observer_issue_exists(title):
        print(f"observer_notify: open Linear issue already exists for: {title}")
        return True
    mutation = {
        "query": (
            "mutation($input: IssueCreateInput!) {"
            " issueCreate(input: $input) { success issue { identifier url } } }"
        ),
        "variables": {
            "input": {"teamId": team, "title": title, "description": body}
        },
    }
    data = _post_json(LINEAR_GQL, mutation, headers)
    issue = (
        (((data or {}).get("data") or {}).get("issueCreate") or {}).get("issue")
        or {}
    )
    print(f"observer_notify: Linear issue {issue.get('identifier')} {issue.get('url')}")
    return True


def notify(title: str, body: str, *, slack: bool = True, linear: bool = True) -> None:
    if not title.startswith(OBSERVER_PREFIX):
        title = f"{OBSERVER_PREFIX} {title}"
    if slack:
        try:
            notify_slack(f"*{title}*\n{body}")
        except Exception as exc:  # noqa: BLE001 — one sink down must not kill the other
            print(f"observer_notify: Slack failed: {exc}", file=sys.stderr)
    if linear:
        try:
            notify_linear(title, body)
        except Exception as exc:  # noqa: BLE001
            print(f"observer_notify: Linear failed: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Observer notification fan-out")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--slack-only", action="store_true")
    parser.add_argument("--linear-only", action="store_true")
    args = parser.parse_args()
    notify(
        args.title,
        args.body,
        slack=not args.linear_only,
        linear=not args.slack_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
