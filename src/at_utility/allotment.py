"""Push regional rate-limit allotments from leader Redis to edge RL Redis.

Leader key:  at:global:quota:{region}  -> integer tokens for the next window
Edge key:    at:global:allotment:{region} (copied) + optional per-tenant caps

Usage (CronJob / local):
  python -m at_utility.allotment --region us-west-2
Env:
  REDIS_LEADER_URL  (required for grant source)
  REDIS_RL_URL      (edge local writable Redis)
  AT_REGION
  ALLOTMENT_DEFAULT (fallback tokens if leader key missing)

KNOWN GAP: this module correctly writes `at:global:allotment:{region}`, but
the request-path token bucket (main.rate_limit -> RedisStore.eval_token_bucket)
does not read it yet — it uses the fixed `Settings.at_rate_limit_rps` /
`at_rate_limit_burst` for every region. Wiring `rate_limit()` to look up this
key as a per-region rate/burst override is still open; until then this cron
is deployed but its output has no consumer. See infra/README.md "Rate limits".
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

import redis.asyncio as aioredis

log = logging.getLogger("at_utility.allotment")


async def refresh_allotment(
    *,
    leader_url: str,
    rl_url: str,
    region: str,
    default_tokens: int,
    ttl_seconds: int = 120,
) -> int:
    leader = aioredis.from_url(leader_url, decode_responses=True)
    rl = aioredis.from_url(rl_url, decode_responses=True)
    try:
        key = f"at:global:quota:{region}"
        raw = await leader.get(key)
        tokens = int(raw) if raw is not None else default_tokens
        dest = f"at:global:allotment:{region}"
        await rl.set(dest, str(tokens), ex=ttl_seconds)
        log.info("allotment region=%s tokens=%s ttl=%s", region, tokens, ttl_seconds)
        return tokens
    finally:
        await leader.aclose()
        await rl.aclose()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(description="Refresh regional quota allotment")
    p.add_argument("--region", default=os.getenv("AT_REGION", "local"))
    p.add_argument(
        "--leader-url",
        default=os.getenv("REDIS_LEADER_URL") or os.getenv("REDIS_WRITE_URL") or "",
    )
    p.add_argument("--rl-url", default=os.getenv("REDIS_RL_URL") or os.getenv("REDIS_URL") or "")
    p.add_argument("--default", type=int, default=int(os.getenv("ALLOTMENT_DEFAULT", "1000")))
    p.add_argument("--ttl", type=int, default=120)
    args = p.parse_args()
    if not args.leader_url or not args.rl_url:
        raise SystemExit("REDIS_LEADER_URL (or REDIS_WRITE_URL) and REDIS_RL_URL required")
    asyncio.run(
        refresh_allotment(
            leader_url=args.leader_url,
            rl_url=args.rl_url,
            region=args.region,
            default_tokens=args.default,
            ttl_seconds=args.ttl,
        )
    )


if __name__ == "__main__":
    main()
