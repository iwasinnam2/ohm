import Link from "next/link";
import { OhmMark } from "./OhmMark";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="site-header__brand">
        <OhmMark className="site-header__mark" />
        <span className="site-header__name">withOhm</span>
      </Link>
      <nav className="site-header__nav" aria-label="Primary">
        <Link href="/docs">Docs</Link>
        <Link href="/billing">Billing</Link>
        <Link href="/" className="site-header__cta">
          Home
        </Link>
      </nav>
    </header>
  );
}
