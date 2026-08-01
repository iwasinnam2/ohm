"""Observer pulse — 15-minute watchdog over the public surface (stdlib only).

Probes the endpoints a paying customer's journey depends on. Any failure is
fanned out to Slack + Linear via observer_notify (dedup keeps repeat probes
from stacking issues) and the process exits non-zero so the workflow run goes
red for observer-meta to see.

Env:
  OHM_ADMIN_KEY   optional — enables the /v1/admin/ops billing-pipeline probe
  plus the observer_notify sink env (SLACK_WEBHOOK_URL, LINEAR_API_KEY, ...).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from observer_notify import notify

API = "https://api.withohm.dev"
WWW = "https://www.withohm.dev"
TIMEOUT = 20


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.status, res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:500]
    except Exception as exc:  # noqa: BLE001 — a dead endpoint is a finding, not a crash
        return 0, f"{type(exc).__name__}: {exc}"


def run_probes() -> list[str]:
    failures: list[str] = []

    def check(name: str, url: str, predicate, headers=None) -> None:
        status, body = _get(url, headers)
        ok, why = predicate(status, body)
        line = f"{'OK  ' if ok else 'FAIL'} {name} ({status}) {url}"
        print(line)
        if not ok:
            failures.append(f"{name}: HTTP {status} — {why}")

    def expect_200(status: int, _body: str):
        return status == 200, "expected 200"

    def expect_health(status: int, body: str):
        if status != 200:
            return False, "expected 200"
        try:
            return bool(json.loads(body).get("ok")), "ok:false in body"
        except ValueError:
            return False, "non-JSON health body"

    check("api health", f"{API}/health", expect_health)
    check("api ready", f"{API}/ready", expect_health)
    check("public stats", f"{API}/v1/public/stats", expect_200)
    check("www home", f"{WWW}/", expect_200)
    check("checkout page", f"{WWW}/billing/intermediate", expect_200)
    check("support page", f"{WWW}/support", expect_200)

    admin_key = os.environ.get("OHM_ADMIN_KEY", "").strip()
    if admin_key:

        def expect_ops(status: int, body: str):
            if status != 200:
                return False, "expected 200"
            try:
                data = json.loads(body)
            except ValueError:
                return False, "non-JSON ops body"
            dlq = data.get("stripe_meter_dlq_len")
            if not data.get("redis_ok"):
                return False, "redis_ok false"
            if dlq != 0:
                return False, f"stripe meter DLQ length {dlq} (underbilling risk)"
            return True, ""

        check(
            "admin ops",
            f"{API}/v1/admin/ops",
            expect_ops,
            headers={"Authorization": f"Bearer {admin_key}"},
        )
    else:
        print("SKIP admin ops (OHM_ADMIN_KEY unset)")

    return failures


def main() -> int:
    failures = run_probes()
    if not failures:
        print("observer-pulse: all probes green")
        return 0
    body = "\n".join(f"- {f}" for f in failures)
    print(f"observer-pulse: {len(failures)} probe(s) failed\n{body}", file=sys.stderr)
    notify(
        f"pulse failure: {len(failures)} probe(s) red",
        body
        + "\n\nRunbook: check `kubectl -n at-utility get pods`, "
        "CloudWatch alarm state, and the latest deploy run.",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
