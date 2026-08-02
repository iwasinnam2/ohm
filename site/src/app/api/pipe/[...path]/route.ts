import { NextRequest, NextResponse } from "next/server";

/**
 * Same-origin proxy so Agent Shell / org console work even when the public
 * API edge has not yet advertised CORS (browser "Failed to fetch").
 */
const UPSTREAM = (
  process.env.OHM_API_URL ||
  process.env.NEXT_PUBLIC_OHM_API_URL ||
  "https://api.withohm.dev"
).replace(/\/$/, "");

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
  const targetPath = path.map(encodeURIComponent).join("/");
  const url = `${UPSTREAM}/${targetPath}${req.nextUrl.search}`;
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (HOP_BY_HOP.has(k)) return;
    if (k === "origin" || k === "referer") return;
    headers.set(key, value);
  });

  let body: ArrayBuffer | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await req.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: req.method,
      headers,
      body: body && body.byteLength > 0 ? body : undefined,
      // Demo traffic should fail fast if the edge is wedged.
      cache: "no-store",
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: {
          message: `Pipe proxy could not reach ${UPSTREAM}: ${String(err)}`,
          type: "proxy_error",
        },
      },
      { status: 502 },
    );
  }

  const out = new NextResponse(upstream.body, { status: upstream.status });
  upstream.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (HOP_BY_HOP.has(k)) return;
    out.headers.set(key, value);
  });
  return out;
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PUT(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
