"""HTTP JSON POST with backoff retry (adapted from forex publish_util)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Optional

log = logging.getLogger("at_utility.http")

DEFAULT_TIMEOUT_S = 30.0
DEFAULT_ATTEMPTS = 3


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: Optional[dict[str, str]] = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    attempts: int = DEFAULT_ATTEMPTS,
    label: str = "post_json",
) -> Optional[dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    hdrs = {"content-type": "application/json", **(headers or {})}
    last_exc: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as res:
                return json.loads(res.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError, TypeError, ValueError) as exc:
            last_exc = exc
            log.warning("%s failed attempt %s/%s (%s)", label, attempt, attempts, exc)
            if attempt < attempts:
                time.sleep(min(2.0 * attempt, 6.0))
    if last_exc is not None:
        log.warning("%s gave up after %s attempts", label, attempts)
    return None
