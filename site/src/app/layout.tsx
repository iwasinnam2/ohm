import type { Metadata } from "next";
import Link from "next/link";
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

// Cap CDN TTL: fully-static prerenders otherwise emit s-maxage=31536000 and
// Amplify's CloudFront serves year-old pages after a deploy. ISR every 5 min
// keeps www fresh without giving up edge caching.
export const revalidate = 300;

const siteUrl = "https://www.withohm.dev";

const description =
  "Interconnectedness and accessibility. Model switching, prompt caching and compliant web browsing — one OpenAI-compatible pipe. Connect it to Cursor, Claude Code, VS Code and more over MCP, bring your own provider keys (BYOK), and pay metered rates on a $0 Intermediate seat.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "withOhm",
    template: "%s · withOhm",
  },
  description,
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
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <div className="atmosphere" aria-hidden="true">
          <div className="atmosphere__current" />
        </div>
        <div className="shell">
          <SiteHeader />
          <main id="main-content" className="shell__main">
            {children}
          </main>
          <footer className="site-footer">
            <span>
              <strong>withOhm</strong> — interconnectedness and accessibility
            </span>
            <nav className="site-footer__legal" aria-label="Legal">
              <Link href="/docs/terms">Terms</Link>
              <Link href="/docs/privacy">Privacy</Link>
              <Link href="/docs/dpa">DPA</Link>
              <Link href="/docs/security">Security</Link>
              <Link href="/docs/legal">Compliance</Link>
              <Link href="/support">Support</Link>
              <Link href="/status">Status</Link>
              <a
                href="https://github.com/iwasinnam2/ohm"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
              <a
                href="https://github.com/iwasinnam2/ohm/discussions"
                target="_blank"
                rel="noopener noreferrer"
              >
                Discussions
              </a>
            </nav>
          </footer>
        </div>
      </body>
    </html>
  );
}
