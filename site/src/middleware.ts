import { NextRequest, NextResponse } from "next/server";

const API_HOSTS = new Set(["api.withohm.dev"]);
const STATUS_HOSTS = new Set(["status.withohm.dev"]);
const FETCH_HOSTS = new Set(["fetch.withohm.dev"]);

/** When true, api.withohm.dev is live on AWS — do not intercept (domain should leave Vercel). */
function apiEdgeLive(): boolean {
  const v = (process.env.API_EDGE_LIVE || "").trim().toLowerCase();
  return v === "1" || v === "true" || v === "yes";
}

function hostname(host: string | null): string {
  if (!host) return "";
  return host.split(":")[0].toLowerCase();
}

/**
 * api.withohm.dev is reserved for the Ohm edge — do not silently serve marketing
 * until DNS points at AWS and API_EDGE_LIVE=1.
 * status.withohm.dev always rewrites to /status.
 * fetch.withohm.dev always rewrites to /fetch (public toy).
 */
export function middleware(request: NextRequest) {
  const host = hostname(request.headers.get("host"));

  if (FETCH_HOSTS.has(host)) {
    const url = request.nextUrl.clone();
    if (url.pathname === "/" || url.pathname === "") {
      url.pathname = "/fetch";
      return NextResponse.rewrite(url);
    }
    if (url.pathname.startsWith("/api/")) {
      return NextResponse.next();
    }
    if (!url.pathname.startsWith("/fetch")) {
      url.pathname = "/fetch";
      return NextResponse.rewrite(url);
    }
    return NextResponse.next();
  }

  if (STATUS_HOSTS.has(host)) {
    const url = request.nextUrl.clone();
    if (url.pathname === "/" || url.pathname === "") {
      url.pathname = "/status";
      return NextResponse.rewrite(url);
    }
    return NextResponse.next();
  }

  if (!API_HOSTS.has(host) || apiEdgeLive()) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  const accept = request.headers.get("accept") || "";
  const wantsJson =
    pathname.startsWith("/v1") ||
    pathname === "/health" ||
    pathname === "/ready" ||
    accept.includes("application/json");

  if (wantsJson) {
    return NextResponse.json(
      {
        ok: false,
        service: "ohm",
        error: {
          message:
            "This host is not serving the public API. Use https://api.withohm.dev/v1. Documentation: https://www.withohm.dev",
          type: "api_unavailable",
          code: "edge_pending",
        },
        docs: "https://www.withohm.dev",
        api: "https://api.withohm.dev/v1",
        acm: "issued",
        cutover: "https://www.withohm.dev/docs/status",
      },
      {
        status: 503,
        headers: {
          "X-Content-Type-Options": "nosniff",
          "Cache-Control": "no-store",
        },
      },
    );
  }

  if (pathname === "/edge-pending") {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/edge-pending";
  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|ohm.svg).*)"],
};
