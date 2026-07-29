import type { Metadata } from "next";
import Link from "next/link";
import { Analytics } from "@vercel/analytics/next";
import { IBM_Plex_Mono, Source_Sans_3, Space_Grotesk } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-source-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

const siteUrl = "https://withohm.dev";

const description =
  "Change one base URL. Keep your prompts, tools, and SDKs. Gain cache, failover, web context, and a bill you can explain.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "withOhm",
    template: "%s · withOhm",
  },
  description,
  icons: {
    icon: "/ohm.svg",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: "withOhm",
    title: "withOhm",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "withOhm",
    description,
  },
  alternates: {
    canonical: "/",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${sourceSans.variable} ${plexMono.variable}`}
    >
      <body>
        <div className="atmosphere" aria-hidden="true">
          <div className="atmosphere__current" />
        </div>
        <div className="shell">
          <SiteHeader />
          <main className="shell__main">{children}</main>
          <footer className="site-footer">
            <span>
              <strong>withOhm</strong> — AI traffic utility
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
