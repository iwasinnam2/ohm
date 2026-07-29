# Region drain drill

Prove clients keep one `base_url` when an edge dies.

## Procedure

1. Pick a non-leader edge (e.g. `eu-west-2`).
2. In Global Accelerator, set that region's endpoint weight to **0** (or remove it).
3. From a client that previously hashed to that region, send 20 chat completions.
4. Expect: HTTP 200, `X-AT-Region` header shows a different healthy region (or traffic shifts at GA).
5. Confirm rate-limit allotments still refresh (`at:global:allotment:{region}` on remaining edges).
6. Confirm replica lag on remaining edges stays within budget.
7. Restore endpoint weight to previous value.
8. Record: start time, drain duration, error count, p99 latency during drain.

## Pass criteria

- Zero client configuration changes
- Error rate during drain &lt; 1% (excluding in-flight TCP resets at cut)
- No sustained 5xx from Rust `/health` on remaining regions

## Fail

If clients hard-fail: check GA health check path (`/health` on port 8081/443), security groups, and that at least two endpoints remain healthy before the drill.
