import Link from "next/link";
import type { Metadata } from "next";
import { PAYG_RATES, formatUsd } from "@/lib/meterRates";

export const metadata: Metadata = {
  title: "Subscriptions",
  description:
    "withOhm — Intermediate ($0 membership + meters, BYOK) and Enterprise design-partner rank.",
};

const TIERS = [
  {
    id: "intermediate",
    name: "Intermediate",
    featured: true,
    price: "Usage-based",
    priceNote: `$0 membership (card on file). Meters: hit ${formatUsd(PAYG_RATES.cache_hit)}/1k · miss ${formatUsd(PAYG_RATES.cache_miss)}/1k · fetch ${formatUsd(PAYG_RATES.web_fetch)}/URL. Optional $29 credit pack.`,
    pros: [
      "Cursor integration — one-click MCP attach",
      "URL search and web context on the pipe",
      "Bring your own provider keys (BYOK)",
      "Real-time model switching with zero local resource drag",
      "Centralised prompt cache and compliant search",
      "Pay for pipe rent you use — not a deadweight seat",
    ],
    cta: {
      href: "/billing/intermediate",
      label: "Subscribe",
    },
  },
  {
    id: "enterprise",
    name: "Enterprise",
    featured: false,
    price: "From $2,500/mo",
    priceNote:
      "Fixed monthly bundles for large-scale operations. Negotiated transaction usage agreements.",
    pros: [
      "Everything in Intermediate",
      "Design-partner rank — negotiate fixed monthly bundles for cache hits, cache misses, and web fetches",
      "Unlimited-feel usage under a salaried fee (modern SMS / minutes / data model)",
      "Weekly live stats emailed with dedicated usage budgets and utilisation",
      "Personal admin contact",
      "Invite to the design-partner forum — converse directly with withOhm engineers",
    ],
    cta: {
      href: "/billing/enterprise",
      label: "Contact Enterprise",
    },
  },
] as const;

export default function SubscriptionsPage() {
  return (
    <>
      <header className="page-head">
        <h1>Subscriptions</h1>
        <p>
          withOhm is usage-led pipe rent for AI software developers: attach once,
          keep your provider keys (BYOK), and pay for cache replay and compliant
          web fetch as you go. Intermediate membership is <strong>$0</strong> with
          a card on file; meters invoice monthly. An optional{" "}
          <strong>$29 credit pack</strong> prepays allowance toward usage — it is
          not a required seat. Enterprise negotiates fixed transactional bundles
          for high-volume scraping.
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
                <Link className="btn btn--primary" href={tier.cta.href}>
                  {tier.cta.label}
                </Link>
              </div>
            </li>
          ))}
        </ul>
        <div className="partner__cta cta-row">
          <Link href="/design-partners" className="link-quiet">
            Apply as founding design partner
          </Link>
          <Link href="/docs/quickstart" className="link-quiet">
            Read the quickstart
          </Link>
          <Link href="/docs/pricing" className="link-quiet">
            Pricing detail
          </Link>
        </div>
        <table className="rate-table" aria-label="Intermediate meter list rates">
          <caption>Intermediate meter list (USD)</caption>
          <thead>
            <tr>
              <th scope="col">Meter</th>
              <th scope="col">Unit</th>
              <th scope="col">List</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Cache hit</td>
              <td>per 1k tokens</td>
              <td>{formatUsd(PAYG_RATES.cache_hit)}</td>
            </tr>
            <tr>
              <td>Cache miss</td>
              <td>per 1k tokens</td>
              <td>{formatUsd(PAYG_RATES.cache_miss)}</td>
            </tr>
            <tr>
              <td>Web fetch</td>
              <td>per URL</td>
              <td>{formatUsd(PAYG_RATES.web_fetch)}</td>
            </tr>
            <tr>
              <td>Membership</td>
              <td>per month</td>
              <td>$0 (card on file)</td>
            </tr>
            <tr>
              <td>Credit pack</td>
              <td>optional prepaid</td>
              <td>$29</td>
            </tr>
          </tbody>
        </table>
        <p className="status-foot">
          Billing plan id for Intermediate is <code>payg</code> in the API and
          Stripe metadata — UI label stays Intermediate.
        </p>
      </div>
    </>
  );
}
