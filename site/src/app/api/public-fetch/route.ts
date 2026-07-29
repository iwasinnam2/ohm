import { NextRequest, NextResponse } from "next/server";

const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 8;
const MAX_BYTES = 400_000;
const WATERMARK =
  "\n\n---\nvia withOhm — compliant fetch for agents · https://withohm.dev/i\n";

const hits = new Map<string, { n: number; reset: number }>();

function clientIp(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}

function rateLimit(ip: string): boolean {
  const now = Date.now();
  const row = hits.get(ip);
  if (!row || now > row.reset) {
    hits.set(ip, { n: 1, reset: now + WINDOW_MS });
    return true;
  }
  if (row.n >= MAX_PER_WINDOW) return false;
  row.n += 1;
  return true;
}

function htmlToText(html: string): string {
  let s = html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, " ");
  s = s.replace(/<\/(p|div|h[1-6]|li|tr|br|section|article)>/gi, "\n");
  s = s.replace(/<[^>]+>/g, " ");
  s = s
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  s = s.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n");
  s = s.replace(/[ \t]{2,}/g, " ").trim();
  if (s.length > 12_000) s = `${s.slice(0, 12_000)}\n…`;
  return s;
}

export async function GET(req: NextRequest) {
  const url = req.nextUrl.searchParams.get("url")?.trim() || "";
  if (!url) {
    return NextResponse.json(
      { error: "Pass ?url=https://… (public http/https only)" },
      { status: 400 },
    );
  }
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return NextResponse.json(
      { error: "Only public http(s) URLs" },
      { status: 400 },
    );
  }
  if (
    ["localhost", "127.0.0.1", "0.0.0.0", "::1"].includes(parsed.hostname) ||
    parsed.hostname.endsWith(".local") ||
    parsed.hostname.endsWith(".internal")
  ) {
    return NextResponse.json(
      { error: "Public hosts only" },
      { status: 400 },
    );
  }

  const ip = clientIp(req);
  if (!rateLimit(ip)) {
    return NextResponse.json(
      {
        error: "Soft rate limit — try again shortly, or get a seat at /i",
        install: "https://withohm.dev/i",
      },
      { status: 429 },
    );
  }

  // Prefer live Ohm pipe when demo key is configured
  const demoKey = (process.env.OHM_DEMO_API_KEY || "").trim();
  const apiBase = (
    process.env.OHM_API_URL ||
    process.env.AT_UTILITY_API_URL ||
    "https://api.withohm.dev"
  ).replace(/\/$/, "");

  if (demoKey) {
    try {
      const res = await fetch(`${apiBase}/v1/chat/completions`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${demoKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "mock",
          messages: [
            {
              role: "user",
              content: "Return the fetched page as clear markdown context.",
            },
          ],
          fetch_web_context: true,
          web_purpose: "public_web_retrieval",
          web_urls: [url],
          web_format: "markdown",
          web_compliance_ack: true,
          terms_ack: true,
          dpa_ack: true,
          cache_control: "no_store",
        }),
        signal: AbortSignal.timeout(45_000),
      });
      const data = (await res.json()) as {
        choices?: { message?: { content?: string } }[];
        error?: { message?: string };
      };
      if (res.ok) {
        const content =
          data.choices?.[0]?.message?.content?.trim() ||
          JSON.stringify(data, null, 2);
        return NextResponse.json({
          url,
          markdown: content + WATERMARK,
          via: "ohm",
          phrase: "compliant fetch for agents",
          install: "https://withohm.dev/i",
        });
      }
    } catch {
      /* fall through to local toy fetch */
    }
  }

  try {
    const res = await fetch(url, {
      redirect: "follow",
      headers: {
        "User-Agent": "withOhm-public-fetch-toy/0.1 (+https://withohm.dev/fetch)",
        Accept: "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
      },
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: `Upstream HTTP ${res.status}`, url },
        { status: 502 },
      );
    }
    const buf = await res.arrayBuffer();
    if (buf.byteLength > MAX_BYTES) {
      return NextResponse.json(
        { error: "Page too large for the public toy" },
        { status: 413 },
      );
    }
    const ctype = res.headers.get("content-type") || "";
    const raw = new TextDecoder("utf-8", { fatal: false }).decode(buf);
    const markdown = (
      ctype.includes("html") ? htmlToText(raw) : raw.slice(0, 12_000)
    ).trim();
    return NextResponse.json({
      url,
      markdown: markdown + WATERMARK,
      via: "toy",
      phrase: "compliant fetch for agents",
      install: "https://withohm.dev/i",
      note: "Public toy preview. Full Cursor pipe: https://withohm.dev/i",
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: err instanceof Error ? err.message : "Fetch failed",
        install: "https://withohm.dev/i",
      },
      { status: 502 },
    );
  }
}
