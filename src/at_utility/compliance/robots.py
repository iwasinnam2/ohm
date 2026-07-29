"""robots.txt respect for public crawls (civil / policy hygiene; default on)."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger("at_utility.compliance.robots")

USER_AGENT = "OhmBot/0.1 (+https://withohm.dev/legal; public-retrieval; respect-robots)"

_cache: dict[str, RobotFileParser] = {}


async def allowed_by_robots(url: str, *, enabled: bool = True, timeout: float = 5.0) -> bool:
    """Return False if robots.txt disallows this UA for the URL path."""
    if not enabled:
        return True

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = _cache.get(robots_url)
    if rp is None:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                res = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
                if res.status_code == 404:
                    # No robots.txt ⇒ treat as allow (public crawl norm)
                    rp.parse([])
                elif res.status_code >= 400:
                    log.info("robots.txt fetch failed %s status=%s; allowing with caution", robots_url, res.status_code)
                    rp.parse([])
                else:
                    rp.parse(res.text.splitlines())
        except Exception as exc:  # noqa: BLE001
            log.info("robots.txt error %s (%s); allowing with caution", robots_url, exc)
            rp.parse([])
        _cache[robots_url] = rp

    try:
        return bool(rp.can_fetch(USER_AGENT, url))
    except Exception:  # noqa: BLE001
        return True


def clear_robots_cache() -> None:
    _cache.clear()
