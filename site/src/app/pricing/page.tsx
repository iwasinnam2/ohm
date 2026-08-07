import Link from "next/link";
import type { Metadata } from "next";
import { StartOrProfileCta } from "@/components/StartOrProfileCta";
import {
  COMMIT_TIERS,
  formatUsd,
  formatUsdMoney,
  PAYG_RATES,
} from "@/lib/meterRates";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "withOhm pricing — $0 Intermediate seat, metered cache and web fetch, optional commit tiers. BYOK; no token wholesale on Intermediate.",
};

export default function PricingPage() {
  return (
    <div className="pricing-page">
      <header className="page-head">
        <p className="marketing-article__eyebrow">Pricing</p>
        <h1>Seat + meters. Not token wholesale.</h1>
        <p>
          Keep your provider keys (BYOK). Pay withOhm for pipe rent — cache hits,
          misses, and compliant web fetch — on a <strong>$0 Intermediate</strong>{" "}
          membership with a card on file.
        </p>
        <div className="cta-row marketing-article__cta">
          <StartOrProfileCta className="btn btn--primary" />
          <Link href="/docs/pricing" className="link-quiet">
            Full rate card
          </Link>
          <Link href="/billing/enterprise" className="link-quiet">
            Enterprise
          </Link>
        </div>
      </header>

      <h2 className="board__label" style={{ marginTop: "2rem" }}>
        Intermediate list rates
      </h2>
      <table className="pricing-page__matrix">
        <thead>
          <tr>
            <th>Meter</th>
            <th>Unit</th>
            <th>List (USD)</th>
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
        </tbody>
      </table>

      <h2 className="board__label">Optional commit tiers</h2>
      <table className="pricing-page__matrix">
        <thead>
          <tr>
            <th>Tier</th>
            <th>Monthly</th>
            <th>Included metered usage</th>
          </tr>
        </thead>
        <tbody>
          {COMMIT_TIERS.map((tier) => (
            <tr key={tier.id}>
              <td>
                <code>{tier.id}</code>
              </td>
              <td>{formatUsdMoney(tier.usd_month)}</td>
              <td>{formatUsdMoney(tier.included_usd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>
        Overage bills at list rates. Pick a tier at{" "}
        <Link href="/subscriptions">Subscriptions</Link> or pass{" "}
        <code>commit</code> to checkout.
      </p>

      <h2 className="board__label">Plans</h2>
      <table className="pricing-page__matrix">
        <thead>
          <tr>
            <th></th>
            <th>Intermediate</th>
            <th>Enterprise</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Membership</td>
            <td>$0 + meters (card on file)</td>
            <td>Contact us</td>
          </tr>
          <tr>
            <td>Model tokens</td>
            <td>BYOK — you pay labs</td>
            <td>BYOK or managed pool terms</td>
          </tr>
          <tr>
            <td>Cache trees</td>
            <td>Included</td>
            <td>Included + org controls</td>
          </tr>
          <tr>
            <td>Org / SSO / FinOps</td>
            <td>Core paths</td>
            <td>Full chaos-governor pack</td>
          </tr>
          <tr>
            <td>Uptime SLA</td>
            <td>—</td>
            <td>Contractual under Enterprise</td>
          </tr>
        </tbody>
      </table>

      <section className="pricing-page__faq" aria-labelledby="pricing-faq">
        <h2 className="board__label" id="pricing-faq">
          Common questions
        </h2>
        <div>
          <h3>Do you resell model tokens on Intermediate?</h3>
          <p>No. BYOK ledgers — labs bill generation; withOhm bills pipe rent.</p>
        </div>
        <div>
          <h3>Are savings figures guaranteed?</h3>
          <p>
            No. <code>/v1/savings</code> is always <code>estimate_only</code>. See{" "}
            <Link href="/product/waste-demo">Waste demo</Link>.
          </p>
        </div>
        <div>
          <h3>Where is the detailed rate card?</h3>
          <p>
            <Link href="/docs/pricing">Docs — Pricing</Link> mirrors invoice
            basis, dunning, and SKU endpoints.
          </p>
        </div>
      </section>
    </div>
  );
}
