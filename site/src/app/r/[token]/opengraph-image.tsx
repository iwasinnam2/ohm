import { ImageResponse } from "next/og";
import { formatUsd, getPublicReceipt } from "@/lib/publicApi";

export const runtime = "nodejs";
export const alt = "withOhm savings receipt";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = "#090c0f";
const PAPER = "#f2ebe0";
const COPPER = "#d08945";
const MUTED = "#9a8f80";

type Props = {
  params: Promise<{ token: string }>;
};

export default async function ReceiptOgImage({ params }: Props) {
  const { token } = await params;
  const data = await getPublicReceipt(token);
  const name = data?.receipt.display_name ?? "A withOhm workspace";
  const saved = data
    ? `~${formatUsd(data.receipt.estimated_upstream_avoided_usd)}`
    : "$—";
  const hitPct = data
    ? `${Math.round((data.receipt.cache_hit_ratio || 0) * 100)}% cache hit ratio`
    : "";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "72px 88px",
          backgroundColor: INK,
          backgroundImage:
            "radial-gradient(900px 420px at 18% 0%, rgba(208,137,69,0.14), transparent)",
          color: PAPER,
          fontFamily: "Georgia, 'Times New Roman', serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 72,
              height: 72,
              borderRadius: 16,
              border: `2px solid ${COPPER}`,
              color: COPPER,
              fontSize: 48,
              fontWeight: 700,
            }}
          >
            Ω
          </div>
          <div style={{ display: "flex", fontSize: 40, color: MUTED }}>
            withOhm savings receipt
          </div>
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 48,
            fontSize: 48,
            maxWidth: 1000,
          }}
        >
          {name} saved
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 8,
            fontSize: 132,
            fontWeight: 700,
            color: COPPER,
          }}
        >
          {saved}
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 36,
            fontSize: 28,
            color: MUTED,
          }}
        >
          {hitPct
            ? `${hitPct} · estimated upstream spend avoided via prompt replay · www.withohm.dev`
            : "estimated upstream spend avoided via prompt replay · www.withohm.dev"}
        </div>
      </div>
    ),
    size,
  );
}
