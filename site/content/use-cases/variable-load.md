CI hours and agent fleets are bursty. Exact-replay turns the second and nth identical call into a Redis HIT. Locality keeps that HIT near the request.

## Summary

- **MISS once, HIT thereafter** — Mechanical suites stop re-buying completions
- **Edge-minded GETs** — Hot path optimized for cache reads
- **Honest streaming limits** — No pretend mid-stream failover ([Streaming](/docs/streaming))
- **Meters scale with crossings** — Pipe rent tracks usage; Intermediate seat stays $0
- **Trees for noisy suites** — Isolate stampeding jobs ([CI preview](/use-cases/ci-preview))

## Why variable load is an Ohm story

Provisioned “AI gateways” sized for peak waste money at idle and still fail isolation. withOhm meters crossings and stores inventory content-addressed — busy tenants generate more HITs; quiet ones do not invent fixed instance rent for replay.

## Anti-pattern: always-on peak capacity for prompts

You overbuy lab tokens and proxy capacity for the one hour CI is red.

## How we win

[Locality & edge](/product/locality) · [Edge docs](/docs/edge) · [Pricing](/pricing) · [$0 seat](/billing/intermediate)
