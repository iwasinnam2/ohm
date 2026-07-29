"""Redis clients: TCP redis-py + optional local-read / leader-write split."""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Optional, Protocol

import redis.asyncio as aioredis

from at_utility.config import Settings

log = logging.getLogger("at_utility.redis")


def tenant_key(tenant: str, kind: str, name: str) -> str:
    """Multi-tenant key convention (adapted from frontend/_lib/redis.js)."""
    return f"at:{tenant}:{kind}:{name}"


def upstash_cmd(url: str, token: str, cmd: list[Any]) -> Any:
    """Raw Upstash REST command array (adapted from _phase1_redis_seat.redis_cmd)."""
    req = urllib.request.Request(
        url,
        data=json.dumps(cmd).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = json.loads(res.read().decode("utf-8"))
    return raw.get("result", raw) if isinstance(raw, dict) else raw


class CacheStore(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    async def incr_by_float(self, key: str, amount: float) -> float: ...
    async def eval_token_bucket(self, key: str, rate: float, burst: float, now: float) -> bool: ...
    async def ping(self) -> bool: ...
    async def close(self) -> None: ...


TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
  tokens = burst
  ts = now
end
local delta = math.max(0, now - ts)
tokens = math.min(burst, tokens + delta * rate)
local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end
redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, 60)
return allowed
"""


class RedisStore:
    """
    Single-endpoint store, or split:
      - read_url: local replica GET (cache hits)
      - write_url: leader SET / metering (cache misses, ledger)
      - rl_url: local writable Redis for regional token buckets (defaults to write)
    """

    def __init__(
        self,
        read_url: str,
        write_url: str | None = None,
        rl_url: str | None = None,
    ):
        write = write_url or read_url
        rl = rl_url or write
        self._read = aioredis.from_url(read_url, decode_responses=True)
        self._write = (
            self._read if write == read_url else aioredis.from_url(write, decode_responses=True)
        )
        self._rl = (
            self._write
            if rl == write
            else (
                self._read
                if rl == read_url
                else aioredis.from_url(rl, decode_responses=True)
            )
        )
        self._read_url = read_url
        self._write_url = write
        self._rl_url = rl

    async def get(self, key: str) -> Optional[str]:
        return await self._read.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if ttl_seconds and ttl_seconds > 0:
            await self._write.set(key, value, ex=ttl_seconds)
        else:
            await self._write.set(key, value)

    async def incr_by_float(self, key: str, amount: float) -> float:
        return float(await self._write.incrbyfloat(key, amount))

    async def eval_token_bucket(self, key: str, rate: float, burst: float, now: float) -> bool:
        result = await self._rl.eval(TOKEN_BUCKET_LUA, 1, key, rate, burst, now)
        return int(result) == 1

    async def ping(self) -> bool:
        await self._write.ping()
        return True

    async def close(self) -> None:
        await self._read.aclose()
        if self._write is not self._read:
            await self._write.aclose()
        if self._rl is not self._read and self._rl is not self._write:
            await self._rl.aclose()


class MemoryStore:
    """In-process fallback for tests / no Redis."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._buckets: dict[str, tuple[float, float]] = {}
        self._counters: dict[str, float] = {}

    async def get(self, key: str) -> Optional[str]:
        if key in self._data:
            return self._data[key]
        if key in self._counters:
            return str(self._counters[key])
        return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._data[key] = value

    async def incr_by_float(self, key: str, amount: float) -> float:
        self._counters[key] = self._counters.get(key, 0.0) + amount
        self._data[key] = str(self._counters[key])
        return self._counters[key]

    async def eval_token_bucket(self, key: str, rate: float, burst: float, now: float) -> bool:
        tokens, ts = self._buckets.get(key, (burst, now))
        tokens = min(burst, tokens + max(0.0, now - ts) * rate)
        if tokens < 1:
            self._buckets[key] = (tokens, now)
            return False
        self._buckets[key] = (tokens - 1, now)
        return True

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None


async def build_store(settings: Settings) -> CacheStore:
    try:
        store = RedisStore(
            settings.redis_url,
            write_url=settings.redis_write_url or None,
            rl_url=settings.redis_rl_url or None,
        )
        await store._read.ping()
        await store._write.ping()
        log.info(
            "connected to redis read=%s write=%s rl=%s",
            store._read_url,
            store._write_url,
            store._rl_url,
        )
        return store
    except Exception as exc:  # noqa: BLE001
        log.warning("redis unavailable (%s); using in-memory store", exc)
        return MemoryStore()
