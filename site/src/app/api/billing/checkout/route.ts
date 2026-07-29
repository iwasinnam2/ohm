import { NextRequest, NextResponse } from "next/server";

/**
 * Proxies self-serve checkout to the Ohm control plane.
 * Set OHM_API_URL (e.g. http://127.0.0.1:8080) — no trailing /v1.
 */
export async function POST(req: NextRequest) {
  const apiRoot = (
    process.env.OHM_API_URL ||
    process.env.AT_UTILITY_API_URL ||
    "http://127.0.0.1:8080"
  ).replace(/\/$/, "");

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const origin = req.nextUrl.origin;
  const payload = {
    plan: body.plan === "enterprise" ? "enterprise" : "payg",
    label: typeof body.label === "string" ? body.label : "",
    email: typeof body.email === "string" ? body.email : "",
    terms_ack: Boolean(body.terms_ack),
    dpa_ack: Boolean(body.dpa_ack),
    success_url:
      typeof body.success_url === "string" && body.success_url
        ? body.success_url
        : `${origin}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url:
      typeof body.cancel_url === "string" && body.cancel_url
        ? body.cancel_url
        : `${origin}/billing/cancel`,
  };

  try {
    const res = await fetch(`${apiRoot}/v1/billing/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
        error: "Cannot reach Ohm API",
        detail: err instanceof Error ? err.message : String(err),
        hint: "Set OHM_API_URL on the site (control plane, e.g. http://127.0.0.1:8080)",
      },
      { status: 503 }
    );
  }
}
