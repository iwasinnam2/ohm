"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { OhmMark } from "./OhmMark";

function navCurrent(
  pathname: string,
  href: string,
): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/subscriptions") {
    return (
      pathname === "/subscriptions" || pathname.startsWith("/billing")
    );
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteHeader() {
  const pathname = usePathname() || "/";

  const links = [
    { href: "/workbench", label: "Shell" },
    { href: "/org", label: "Org" },
    { href: "/connections", label: "Connections" },
    { href: "/docs", label: "Docs" },
    { href: "/subscriptions", label: "Billing" },
    { href: "/", label: "Home" },
  ] as const;

  return (
    <header className="site-header">
      <Link href="/" className="site-header__brand">
        <OhmMark className="site-header__mark" />
        <span className="site-header__name">withOhm</span>
      </Link>
      <nav className="site-header__nav" aria-label="Primary">
        {links.map((link) => {
          const current = navCurrent(pathname, link.href);
          return (
            <Link
              key={link.href + link.label}
              href={link.href}
              aria-current={current ? "page" : undefined}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
