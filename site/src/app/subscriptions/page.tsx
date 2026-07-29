import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Subscriptions",
  description:
    "withOhm subscriptions — free trial, Intermediate, and Enterprise design-partner rank for high-volume AI workflows.",
};

const TIERS = [
  {
    id: "trial",
    name: "Free trial",
    featured: false,
    price: "$0 for 30 days",
    priceNote:
      "Then $29/mo. Payment details required to activate. A $0.01 verification charge confirms account legitimacy and subscription recurrence.",
    pros: [
      "Full access to withOhm architecture and built-in features for 30 days",
      "Dynamic model switching, web browse, and URL scrape on the pipe",
      "Converts to Intermediate at $29/mo when the trial ends",
    ],
    cta: { href: "/billing", label: "Start free trial", external: false },
  },
  {
    id: "intermediate",
    name: "Intermediate",
    featured: true,
    price: "$29 / month",
    priceNote: "Self-serve seat for AI software developers.",
    pros: [
      "Cursor integration — one-click MCP attach",
      "URL search and web context on the pipe",
      "Proxy-managed keys for streamlined upstream access",
      "Real-time model switching with zero local resource drag",
      "Centralised prompt cache and compliant search",
    ],
    cta: { href: "/billing", label: "Subscribe", external: false },
  },
  {
    id: "enterprise",
    name: "Enterprise",
    featured: false,
    price: "Custom",
    priceNote:
      "Design-partner rank for large-scale operations. Negotiated transaction usage agreements.",
    pros: [
      "Everything in Intermediate",
      "Design-partner rank — negotiate fixed monthly bundles for cache hits, cache misses, and web fetches",
      "Unlimited-feel usage under a salaried fee (modern SMS / minutes / data model)",
      "Weekly live stats emailed with dedicated usage budgets and utilisation",
      "Personal admin contact",
      "Invite to the design-partner forum — converse directly with withOhm engineers",
    ],
    cta: {
      href: "mailto:partners@withohm.dev?subject=withOhm%20Enterprise%20%2F%20design%20partner",
      label: "Contact Enterprise",
      external: true,
    },
  },
] as const;

export default function SubscriptionsPage() {
  return (
    <>
      <header className="page-head">
        <h1>Subscriptions</h1>
        <p>
          withOhm offers a monthly premium for exclusive use of its architecture
          and built-in features. This subscription is tailored toward AI software
          developers who wish to streamline their workflow and integrate the
          withOhm infrastructure into their builds. For $29 monthly, developers
          can switch models dynamically in real time, browse the web, scrape
          URLs — with zero rate limits, zero latency, zero local resources, and
          zero resistance. This subscription covers the encompassing network of
          withOhm&apos;s features: complete streamlining of AI usage, centralised
          cache prompts, and powerful search with full legal compliance. Join
          now and experience the future of AI software development — one where
          you aren&apos;t weighed down by anything, at all.
        </p>
      </header>

      <div className="partner">
        <ul className="tier-grid">
          {TIERS.map((tier) => (
            <li
              key={tier.id}
              className={`tier${tier.featured ? " tier--featured" : ""}`}
            >
              <h2 className="tier__name">{tier.name}</h2>
              <p className="tier__price">
                {tier.price}
                <span>{tier.priceNote}</span>
              </p>
              <ul className="tier__pros">
                {tier.pros.map((pro) => (
                  <li key={pro}>{pro}</li>
                ))}
              </ul>
              <div className="tier__cta">
                {tier.cta.external ? (
                  <a className="btn btn--primary" href={tier.cta.href}>
                    {tier.cta.label}
                  </a>
                ) : (
                  <Link className="btn btn--primary" href={tier.cta.href}>
                    {tier.cta.label}
                  </Link>
                )}
              </div>
            </li>
          ))}
        </ul>
        <div className="partner__cta cta-row">
          <Link href="/docs/quickstart" className="link-quiet">
            Read the quickstart
          </Link>
          <Link href="/docs/pricing" className="link-quiet">
            Pricing detail
          </Link>
        </div>
      </div>
    </>
  );
}
