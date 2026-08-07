import { NextResponse } from "next/server";

/**
 * Public mock-only proof session for /demo.
 * Requires OHM_DEMO_API_KEY on Amplify (dedicated proof tenant — not a paying key).
 */
export async function GET() {
  const key = (process.env.OHM_DEMO_API_KEY || "").trim();
  const headers = {
    "Cache-Control": "no-store, no-cache, must-revalidate",
  };
  if (!key.startsWith("sk-at-")) {
    return NextResponse.json(
      {
        available: false,
        error:
          "Public proof key not configured. Paste a sk-at-… key or get a $0 seat.",
      },
      { status: 503, headers },
    );
  }
  return NextResponse.json(
    {
      available: true,
      apiKey: key,
      model: "mock",
      note: "Public proof key — mock model only. Get a private key for real models and bounty credit.",
    },
    { headers },
  );
}
