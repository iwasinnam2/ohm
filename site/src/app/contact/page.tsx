import type { Metadata } from "next";
import Link from "next/link";
import { EnterpriseApplicationForm } from "@/components/EnterpriseApplicationForm";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Contact withOhm — enterprise inquiry, design partners, and support for the exact-replay pipe.",
};

export default function ContactPage() {
  return (
    <>
      <header className="page-head">
        <p className="marketing-article__eyebrow">Resources</p>
        <h1>Contact</h1>
        <p>
          Enterprise chaos-governor conversations, design-partner applications,
          and day-to-day support — pick the path that matches.
        </p>
        <div className="cta-row marketing-article__cta">
          <Link href="/support" className="link-quiet">
            Support
          </Link>
          <Link href="/design-partners" className="link-quiet">
            Design partners
          </Link>
          <Link href="/billing/intermediate" className="link-quiet">
            Self-serve Intermediate
          </Link>
        </div>
      </header>

      <section className="contact-paths" aria-labelledby="contact-paths-label">
        <h2 id="contact-paths-label" className="board__label">
          Paths
        </h2>
        <ul className="board__grid marketing-index">
          <li>
            <Link href="/billing/enterprise" className="card card--tap">
              <p className="card__eyebrow">Enterprise</p>
              <h3 className="card__title">Chaos governor</h3>
              <p className="card__desc">
                SSO, ledger, policy, managed capacity — from $2,500/month.
                Application form below or on the Enterprise page.
              </p>
              <span className="card__go">Enterprise page →</span>
            </Link>
          </li>
          <li>
            <Link href="/design-partners" className="card card--tap">
              <p className="card__eyebrow">Partners</p>
              <h3 className="card__title">Founding design partners</h3>
              <p className="card__desc">
                Complimentary 90-day seat for builders who will quote and share
                usage before/after.
              </p>
              <span className="card__go">Apply →</span>
            </Link>
          </li>
          <li>
            <Link href="/support/query" className="card card--tap">
              <p className="card__eyebrow">Help</p>
              <h3 className="card__title">Support query</h3>
              <p className="card__desc">
                Intermediate seat and pipe questions — use the support form.
              </p>
              <span className="card__go">Open form →</span>
            </Link>
          </li>
        </ul>
      </section>

      <section aria-labelledby="enterprise-form-label" className="contact-form">
        <h2 id="enterprise-form-label" className="board__label">
          Enterprise inquiry
        </h2>
        <p style={{ color: "var(--muted)", maxWidth: "34rem" }}>
          Same application as{" "}
          <Link href="/billing/enterprise">Enterprise billing</Link> — volume
          projections, terms/DPA ack, and how to reach you.
        </p>
        <EnterpriseApplicationForm />
      </section>

      <p className="marketing-article__back">
        <Link href="/resources">All resources →</Link>
      </p>
    </>
  );
}
