import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt =
  "withOhm — model switching, prompt caching and compliant web browsing over one OpenAI-compatible pipe";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = "#0a0a0c";
const PAPER = "#f2ebe0";
const COPPER = "#a855f7";
const MUTED = "#9b9690";

export default function OpengraphImage() {
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
            "radial-gradient(900px 420px at 18% 0%, rgba(168,85,247,0.18), transparent)",
          color: PAPER,
          fontFamily: "Georgia, 'Times New Roman', serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 120,
              height: 120,
              borderRadius: 24,
              border: `2px solid ${COPPER}`,
              color: COPPER,
              fontSize: 84,
              fontWeight: 700,
            }}
          >
            Ω
          </div>
          <div style={{ display: "flex", fontSize: 92, fontWeight: 700 }}>
            withOhm
          </div>
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 44,
            fontSize: 36,
            lineHeight: 1.35,
            maxWidth: 940,
            color: PAPER,
          }}
        >
          Model switching, prompt caching and compliant web browsing — one
          OpenAI-compatible pipe for Cursor over MCP.
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 40,
            fontSize: 26,
            color: MUTED,
          }}
        >
          BYOK · metered rates · $0 Intermediate seat · www.withohm.dev
        </div>
      </div>
    ),
    size,
  );
}
