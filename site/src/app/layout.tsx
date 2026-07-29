import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Analytics } from "@vercel/analytics/next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Syne } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

const siteUrl = "https://withohm.dev";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Ohm",
    template: "%s · Ohm",
  },
  description:
    "Change one base URL. Keep your prompts, tools, and SDKs. Gain cache, failover, web context, and a bill you can explain.",
  icons: {
    icon: "/ohm.svg",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: "Ohm",
    title: "Ohm",
    description:
      "Change one base URL. Keep your prompts, tools, and SDKs. Gain cache, failover, web context, and a bill you can explain.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Ohm",
    description:
      "Change one base URL. Keep your prompts, tools, and SDKs. Gain cache, failover, web context, and a bill you can explain.",
  },
  alternates: {
    canonical: "/",
  },
};

function edgeBanner(): { live: boolean; text: ReactNode } {
  const live =
    process.env.API_EDGE_LIVE === "1" ||
    process.env.API_EDGE_LIVE === "true" ||
    process.env.API_EDGE_LIVE === "yes";
  if (live) {
    return {
      live: true,
      text: (
        <>
          <strong>Live:</strong> docs on <code>withohm.dev</code> · API{" "}
          <code>https://api.withohm.dev/v1</code>.{" "}
          <Link href="/status">Status</Link>
        </>
      ),
    };
  }
  return {
    live: false,
    text: (
      <>
        <strong>MVP:</strong> docs on <code>withohm.dev</code> · chat edge =
        local <code>:8081</code> (or your deploy) ·{" "}
        <code>api.withohm.dev</code> returns edge-pending until AWS cutover.{" "}
        <Link href="/docs/status">Status</Link>
      </>
    ),
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const banner = edgeBanner();
  return (
    <html lang="en" className={`${syne.variable} ${plex.variable} ${plexMono.variable}`}>
      <body>
        <div className="atmosphere" aria-hidden="true">
          <div className="atmosphere__current" />
        </div>
        <div className="shell">
          <p className="edge-banner" role="status">
            {banner.text}
          </p>
          <SiteHeader />
          <main className="shell__main">{children}</main>
          <footer className="site-footer">
            <span>
              <strong>Ohm</strong> — AI traffic utility
            </span>
            <nav className="site-footer__legal" aria-label="Legal">
              <Link href="/docs/terms">Terms</Link>
              <Link href="/docs/privacy">Privacy</Link>
              <Link href="/docs/dpa">DPA</Link>
              <Link href="/docs/security">Security</Link>
              <Link href="/docs/legal">Compliance</Link>
              <Link href="/status">Status</Link>
            </nav>
          </footer>
        </div>
        <Analytics />
      </body>
    </html>
  );
}
