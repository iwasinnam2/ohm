/** Intermediate PAYG list rates (USD) — mirrors at_utility.config defaults. */
export const PAYG_RATES = {
  cache_hit: 0.0005,
  cache_miss: 0.002,
  web_fetch: 0.001,
} as const;

export const METER_LABELS = {
  cache_hit: "Cache hit",
  cache_miss: "Cache miss",
  web_fetch: "Web fetch (URL)",
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
