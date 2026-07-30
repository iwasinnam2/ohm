import { NextRequest, NextResponse } from "next/server";

/**
 * Proxies the authenticated $29 credit pack top-up to the Ohm control plane.
 * Requires Authorization: Bearer sk-at-… (the tenant's withOhm key).
 */
export async function POST(req: NextRequest) {
  const apiRoot = (
    process.env.OHM_API_URL ||
    process.env.AT_UTILITY_API_URL ||
    "http://127.0.0.1:8080"
  ).replace(/\/$/, "");

  const authorization = req.headers.get("authorization") || "";
  if (!authorization.toLowerCase().startsWith("bearer ")) {
    return NextResponse.json(
      { error: "Authorization: Bearer sk-at-… required" },
      { status: 401 },
    );
  }

  const origin = req.nextUrl.origin;
  const payload = {
    success_url: `${origin}/billing/success?topup=1`,
    cancel_url: `${origin}/billing/cancel`,
  };

  try {
    const res = await fetch(`${apiRoot}/v1/billing/topup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authorization,
      },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    let data: unknown = null;
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: text || "Upstream error" };
    }
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json(
      {
        error: "Cannot reach withOhm API",
        detail: err instanceof Error ? err.message : String(err),
      },
      { status: 503 },
    );
  }
}
