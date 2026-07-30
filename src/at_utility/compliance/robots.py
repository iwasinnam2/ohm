"""robots.txt respect for public crawls (civil / policy hygiene; default on)."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger("at_utility.compliance.robots")

USER_AGENT = "OhmBot/0.1 (+https://www.withohm.dev/docs/legal; public-retrieval; respect-robots)"

_cache: dict[str, RobotFileParser | None] = {}


async def allowed_by_robots(url: str, *, enabled: bool = True, timeout: float = 5.0) -> bool:
    """Return False if robots.txt disallows this UA, or if robots cannot be fetched.

    Fail-closed on network/parse errors (marketplace / compliance honesty).
    Missing robots.txt (HTTP 404) still allows the crawl (public-web norm).
    """
    if not enabled:
        return True

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    if robots_url in _cache:
        rp = _cache[robots_url]
        if rp is None:
            return False
        try:
            return bool(rp.can_fetch(USER_AGENT, url))
        except Exception:  # noqa: BLE001
            return False

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            res = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
            if res.status_code == 404:
                # No robots.txt ⇒ treat as allow (public crawl norm)
                rp.parse([])
            elif res.status_code >= 400:
                log.info(
                    "robots.txt fetch failed %s status=%s; denying (fail-closed)",
                    robots_url,
                    res.status_code,
                )
                _cache[robots_url] = None
                return False
            else:
                rp.parse(res.text.splitlines())
    except Exception as exc:  # noqa: BLE001
        log.info("robots.txt error %s (%s); denying (fail-closed)", robots_url, exc)
        _cache[robots_url] = None
        return False

    _cache[robots_url] = rp
    try:
        return bool(rp.can_fetch(USER_AGENT, url))
    except Exception:  # noqa: BLE001
        return False


def clear_robots_cache() -> None:
    _cache.clear()
