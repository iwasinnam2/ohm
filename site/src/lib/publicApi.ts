/**
 * Read-only helpers for the unauthenticated public API surface
 * (savings receipts + aggregate stats). Server-side only.
 */

const API_ROOT = (
  process.env.OHM_API_URL ||
  process.env.AT_UTILITY_API_URL ||
  "https://api.withohm.dev"
).replace(/\/$/, "");

export type PublicReceipt = {
  token: string;
  display_name: string;
  created_at: number;
  period: string;
  cache_hit_tokens: number;
  cache_hit_ratio: number;
  requests: number;
  estimated_upstream_avoided_usd: number;
  estimate_only: boolean;
};

export type PublicReceiptResponse = {
  receipt: PublicReceipt;
  receipt_url: string;
  badge_image_url: string;
  badge_markdown: string;
};

export type PublicStats = {
  cache_hit_tokens: number;
  estimated_upstream_avoided_usd: number;
  receipts_minted: number;
};

export async function getPublicReceipt(
  token: string
): Promise<PublicReceiptResponse | null> {
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(token)) return null;
  try {
    const res = await fetch(
      `${API_ROOT}/v1/public/receipts/${encodeURIComponent(token)}`,
      { next: { revalidate: 3600 } }
    );
    if (!res.ok) return null;
    return (await res.json()) as PublicReceiptResponse;
  } catch {
    return null;
  }
}

export async function getPublicStats(): Promise<PublicStats | null> {
  try {
    const res = await fetch(`${API_ROOT}/v1/public/stats`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return (await res.json()) as PublicStats;
  } catch {
    return null;
  }
}

export function formatUsd(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  });
}
