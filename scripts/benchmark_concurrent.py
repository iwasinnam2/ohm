"""Concurrent chat benchmark (target band: 50–200 streams)."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


async def one(client: httpx.AsyncClient, sem: asyncio.Semaphore, i: int) -> float:
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": f"bench-{i}"}],
    }
    async with sem:
        t0 = time.perf_counter()
        for attempt in range(8):
            res = await client.post("/v1/chat/completions", json=payload)
            if res.status_code != 429:
                res.raise_for_status()
                return (time.perf_counter() - t0) * 1000.0
            await asyncio.sleep(0.05 * (attempt + 1))
        res.raise_for_status()
        return (time.perf_counter() - t0) * 1000.0


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8080")
    p.add_argument("--key", default="sk-at-dev")
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--concurrency", type=int, default=50)
    args = p.parse_args()

    headers = {"Authorization": f"Bearer {args.key}"}
    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient(base_url=args.base, headers=headers, timeout=60.0) as client:
        latencies = await asyncio.gather(*[one(client, sem, i) for i in range(args.n)])
    print(
        f"n={args.n} concurrency={args.concurrency} "
        f"p50={statistics.median(latencies):.1f}ms "
        f"p95={statistics.quantiles(latencies, n=20)[18]:.1f}ms "
        f"max={max(latencies):.1f}ms"
    )


if __name__ == "__main__":
    asyncio.run(main())
