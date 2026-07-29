import { NextRequest, NextResponse } from "next/server";
import { METER_LABELS, PAYG_RATES, type MeterKey } from "@/lib/meterRates";

const ADMIN_TO = "admin@withohm.dev";
const METERS: MeterKey[] = ["cache_hit", "cache_miss", "web_fetch"];

type MeterPayload = {
  expected?: number;
  actual?: number;
  desired_ppu?: number;
  payg_list?: number;
};

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export async function POST(req: NextRequest) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      {
        error: "Enterprise applications are not configured",
        detail: "Set RESEND_API_KEY on the site deployment.",
      },
      { status: 503 },
    );
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const email = typeof body.email === "string" ? body.email.trim() : "";
  const organisation =
    typeof body.organisation === "string" ? body.organisation.trim() : "";
  const business =
    typeof body.business === "string" ? body.business.trim() : "";
  const termsAck = Boolean(body.terms_ack);
  const dpaAck = Boolean(body.dpa_ack);
  const metersRaw =
    body.meters && typeof body.meters === "object"
      ? (body.meters as Record<string, MeterPayload>)
      : {};

  if (!email || !organisation || business.length < 40) {
    return NextResponse.json(
      {
        error:
          "email, organisation, and a business description (40+ chars) are required",
      },
      { status: 400 },
    );
  }
  if (!termsAck || !dpaAck) {
    return NextResponse.json(
      { error: "Terms and DPA acknowledgement required" },
      { status: 400 },
    );
  }

  const meterLines = METERS.map((key) => {
    const m = metersRaw[key] || {};
    return `${METER_LABELS[key]}:
  expected: ${Number(m.expected) || 0}
  actual: ${Number(m.actual) || 0}
  desired_ppu: $${Number(m.desired_ppu) || 0}
  intermediate_payg_list: $${PAYG_RATES[key]}`;
  }).join("\n\n");

  const text = `withOhm Enterprise application

Organisation: ${organisation}
Email: ${email}

--- Meters ---
${meterLines}

--- Business ---
${business}

Terms ack: ${termsAck}
DPA ack: ${dpaAck}
`;

  const html = `
    <h1>withOhm Enterprise application</h1>
    <p><strong>Organisation:</strong> ${esc(organisation)}</p>
    <p><strong>Email:</strong> ${esc(email)}</p>
    <h2>Meters</h2>
    ${METERS.map((key) => {
      const m = metersRaw[key] || {};
      return `<h3>${esc(METER_LABELS[key])}</h3>
        <ul>
          <li>Expected: ${Number(m.expected) || 0}</li>
          <li>Actual: ${Number(m.actual) || 0}</li>
          <li>Desired PPU: $${Number(m.desired_ppu) || 0}</li>
          <li>Intermediate PAYG list: $${PAYG_RATES[key]}</li>
        </ul>`;
    }).join("")}
    <h2>Business</h2>
    <pre style="white-space:pre-wrap;font-family:inherit">${esc(business)}</pre>
  `;

  const from =
    process.env.RESEND_FROM ||
    "withOhm Applications <partners@withohm.dev>";

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to: [ADMIN_TO],
        reply_to: email,
        subject: `Enterprise application — ${organisation}`,
        text,
        html,
      }),
    });
    const data = (await res.json().catch(() => ({}))) as {
      message?: string;
      id?: string;
    };
    if (!res.ok) {
      return NextResponse.json(
        {
          error: "Failed to send application email",
          detail: data.message || `Resend ${res.status}`,
        },
        { status: 502 },
      );
    }
    return NextResponse.json({ ok: true, id: data.id });
  } catch (err) {
    return NextResponse.json(
      {
        error: "Failed to reach mail provider",
        detail: err instanceof Error ? err.message : String(err),
      },
      { status: 503 },
    );
  }
}
