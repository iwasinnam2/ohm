"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { OhmMark } from "./OhmMark";
import { StartOrProfileCta } from "./StartOrProfileCta";
import { PRODUCT_INDEX } from "@/lib/productMeta";
import { RESOURCES_INDEX } from "@/lib/resourcesMeta";
import { USE_CASE_INDEX } from "@/lib/useCasesMeta";

function navCurrent(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/pricing") {
    return pathname === "/pricing" || pathname.startsWith("/subscriptions");
  }
  if (href === "/resources") {
    return (
      pathname === "/resources" ||
      pathname === "/changelog" ||
      pathname === "/security" ||
      pathname === "/contact" ||
      pathname.startsWith("/support")
    );
  }
  if (href === "/profile") {
    return pathname === "/profile" || pathname.startsWith("/keys");
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
export function SiteHeader() {
  const pathname = usePathname() || "/";

  const utility = [
    { href: "/workbench", label: "Shell" },
    { href: "/keys", label: "Keys" },
    { href: "/org", label: "Analytics" },
  ] as const;

  return (
    <header className="site-header">
      <Link href="/" className="site-header__brand">
        <OhmMark className="site-header__mark" />
        <span className="site-header__name">withOhm</span>
      </Link>
      <nav className="site-header__nav" aria-label="Primary">
        <div className="site-header__mega">
          <Link
            href="/product"
            className="site-header__mega-trigger"
            aria-current={navCurrent(pathname, "/product") ? "page" : undefined}
          >
            Product
          </Link>
          <div className="site-header__mega-panel" role="group" aria-label="Product">
            {PRODUCT_INDEX.map((item) => (
              <Link key={item.slug} href={`/product/${item.slug}`}>
                <span className="site-header__mega-title">{item.title}</span>
                <span className="site-header__mega-desc">{item.description}</span>
              </Link>
            ))}
            <Link href="/product" className="site-header__mega-all">
              All product →
            </Link>
          </div>
        </div>

        <div className="site-header__mega">
          <Link
            href="/use-cases"
            className="site-header__mega-trigger"
            aria-current={
              navCurrent(pathname, "/use-cases") ? "page" : undefined
            }
          >
            Solutions
          </Link>
          <div
            className="site-header__mega-panel"
            role="group"
            aria-label="Solutions"
          >
            {USE_CASE_INDEX.map((item) => (
              <Link key={item.slug} href={`/use-cases/${item.slug}`}>
                <span className="site-header__mega-title">{item.title}</span>
                <span className="site-header__mega-desc">{item.description}</span>
              </Link>
            ))}
            <Link href="/use-cases" className="site-header__mega-all">
              All solutions →
            </Link>
          </div>
        </div>

        <Link
          href="/docs"
          aria-current={navCurrent(pathname, "/docs") ? "page" : undefined}
        >
          Docs
        </Link>
        <Link
          href="/pricing"
          aria-current={navCurrent(pathname, "/pricing") ? "page" : undefined}
        >
          Pricing
        </Link>

        <div className="site-header__mega">
          <Link
            href="/resources"
            className="site-header__mega-trigger"
            aria-current={
              navCurrent(pathname, "/resources") ? "page" : undefined
            }
          >
            Resources
          </Link>
          <div
            className="site-header__mega-panel"
            role="group"
            aria-label="Resources"
          >
            {RESOURCES_INDEX.map((item) => (
              <Link key={item.slug} href={item.href}>
                <span className="site-header__mega-title">{item.title}</span>
                <span className="site-header__mega-desc">{item.description}</span>
              </Link>
            ))}
            <Link href="/resources" className="site-header__mega-all">
              All resources →
            </Link>
          </div>
        </div>

        <span className="site-header__util" aria-hidden="true" />
        {utility.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="site-header__util-link"
            aria-current={navCurrent(pathname, link.href) ? "page" : undefined}
          >
            {link.label}
          </Link>
        ))}
        <StartOrProfileCta className="site-header__cta" />
      </nav>
    </header>
  );
}
