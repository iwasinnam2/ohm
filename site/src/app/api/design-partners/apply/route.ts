import { NextRequest, NextResponse } from "next/server";

const ADMIN_TO = "admin@withohm.dev";

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
        error: "Design-partner applications are not configured",
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
  const name = typeof body.name === "string" ? body.name.trim() : "";
  const organisation =
    typeof body.organisation === "string" ? body.organisation.trim() : "";
  const handle = typeof body.handle === "string" ? body.handle.trim() : "";
  const useCase =
    typeof body.use_case === "string" ? body.use_case.trim() : "";
  const pains = Array.isArray(body.pains)
    ? body.pains.filter((p): p is string => typeof p === "string")
    : [];
  const termsAck = Boolean(body.terms_ack);
  const dpaAck = Boolean(body.dpa_ack);
  const quoteOk = Boolean(body.quote_ok);

  if (!email || !name || useCase.length < 40) {
    return NextResponse.json(
      {
        error:
          "email, name, and a use-case description (40+ chars) are required",
      },
      { status: 400 },
    );
  }
  if (!termsAck || !dpaAck || !quoteOk) {
    return NextResponse.json(
      { error: "Terms, DPA, and quote acknowledgement required" },
      { status: 400 },
    );
  }

  const label = organisation || handle || name;
  const text = `withOhm founding design-partner application

Name: ${name}
Email: ${email}
Organisation: ${organisation || "(solo)"}
Handle: ${handle || "(none)"}
Pains: ${pains.join(", ") || "(none selected)"}

--- Use case ---
${useCase}

Quote OK: ${quoteOk}
Terms ack: ${termsAck}
DPA ack: ${dpaAck}

--- Ops ---
Issue key: POST /v1/admin/tenants plan=design_partner label=${label}
`;

  const html = `
    <h1>Founding design-partner application</h1>
    <p><strong>Name:</strong> ${esc(name)}</p>
    <p><strong>Email:</strong> ${esc(email)}</p>
    <p><strong>Organisation:</strong> ${esc(organisation || "(solo)")}</p>
    <p><strong>Handle:</strong> ${esc(handle || "(none)")}</p>
    <p><strong>Pains:</strong> ${esc(pains.join(", ") || "(none)")}</p>
    <h2>Use case</h2>
    <pre style="white-space:pre-wrap;font-family:inherit">${esc(useCase)}</pre>
    <p>Quote OK: ${quoteOk} · Terms: ${termsAck} · DPA: ${dpaAck}</p>
    <p><code>plan=design_partner</code> label=<code>${esc(label)}</code></p>
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
        subject: `Design partner — ${label}`,
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
