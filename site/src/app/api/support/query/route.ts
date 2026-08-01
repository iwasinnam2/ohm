import { NextRequest, NextResponse } from "next/server";

// Support queries land at queries@withohm.dev once the mailbox/forwarding
// exists; until then SUPPORT_TO is unset and delivery falls back to admin@.
const SUPPORT_TO = process.env.SUPPORT_TO || "admin@withohm.dev";

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
        error: "Support queries are not configured",
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
  const subject = typeof body.subject === "string" ? body.subject.trim() : "";
  const message = typeof body.message === "string" ? body.message.trim() : "";

  if (!email || !subject || message.length < 10) {
    return NextResponse.json(
      { error: "email, subject, and a message (10+ chars) are required" },
      { status: 400 },
    );
  }
  if (subject.length > 200 || message.length > 5000) {
    return NextResponse.json(
      { error: "subject or message too long" },
      { status: 400 },
    );
  }

  const text = `withOhm support query

From: ${email}
Subject: ${subject}

${message}
`;

  const html = `
    <h1>withOhm support query</h1>
    <p><strong>From:</strong> ${esc(email)}</p>
    <p><strong>Subject:</strong> ${esc(subject)}</p>
    <pre style="white-space:pre-wrap;font-family:inherit">${esc(message)}</pre>
  `;

  const from =
    process.env.RESEND_FROM || "withOhm Support <partners@withohm.dev>";

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to: [SUPPORT_TO],
        reply_to: email,
        subject: `Support query — ${subject}`,
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
          error: "Failed to send support query",
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
