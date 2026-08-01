/**
 * Rates come from the canonical rate card (pricing/rate_card.v2.json).
 * Python config defaults are asserted equal by tests/test_rate_card.py —
 * change the JSON (by issuing a new version) and everything follows.
 *
 * ./rate_card.v2.json is a committed copy of pricing/rate_card.v2.json:
 * Vercel deploys upload only site/, so the site cannot import outside it.
 * When issuing a new rate card version, re-copy the JSON here.
 */
import rateCard from "./rate_card.v2.json";

export const RATE_CARD_VERSION = rateCard.version;

export const PAYG_RATES = {
  /** USD per 1k tokens (cache hit) */
  cache_hit: rateCard.meters.cache_hit.usd,
  /** USD per 1k tokens (cache miss) */
  cache_miss: rateCard.meters.cache_miss.usd,
  /** USD per URL */
  web_fetch: rateCard.meters.web_fetch.usd,
} as const;

export type CommitTier = {
  id: string;
  usd_month: number;
  included_usd: number;
};

export const COMMIT_TIERS: readonly CommitTier[] = rateCard.commit_tiers;

export const ENTERPRISE_FROM_USD_MONTH = rateCard.enterprise_from_usd_month;

export const METER_LABELS = {
  cache_hit: "Cache hit (per 1k tokens)",
  cache_miss: "Cache miss (per 1k tokens)",
  web_fetch: "Web fetch (per URL)",
} as const;

export type MeterKey = keyof typeof PAYG_RATES;

export const PROJECTION_VOLUMES = [1000, 2000, 5000, 10000] as const;

export function formatUsd(n: number, digits = 4): string {
  if (n >= 0.01 || n === 0) {
    return `$${n.toFixed(Math.min(digits, 2))}`;
  }
  return `$${n.toFixed(digits)}`;
}

export function formatUsdMoney(n: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}
