import Link from "next/link";
import type { Metadata } from "next";
import { DualCrossingAid } from "@/components/DualCrossingAid";
import { EnablementFeatures } from "@/components/EnablementFeatures";
import { PRODUCT_INDEX } from "@/lib/product";

export const metadata: Metadata = {
  title: "Product — what is withOhm",
  description:
    "withOhm is an AI traffic utility: ephemeral exact-replay inventory and a durable governance pipeline meeting at a metered HIT/MISS crossing.",
};

export default function ProductIndexPage() {
  const deepLinks = PRODUCT_INDEX.filter((p) => p.slug !== "what-is-withohm");

  return (
    <>
      <header className="page-head product-hero">
        <p className="product-hero__eyebrow">Product</p>
        <h1>What is withOhm</h1>
        <p className="product-hero__lede">
          An AI traffic utility that rents the pipe — not the model. Exact-match
          replay stops mechanical agent loops from re-paying prefill. Governance
          meters every crossing, gates compliant web context, and keeps a clean
          ledger.
        </p>
        <div className="cta-row product-hero__cta">
          <Link href="/signup" className="btn btn--primary">
            Create Account
          </Link>
          <Link href="/product/waste-demo" className="btn btn--login">
            Waste demo
          </Link>
          <Link href="/docs/architecture" className="link-quiet">
            Architecture deep dive
          </Link>
        </div>
      </header>

      <DualCrossingAid flashy />

      <EnablementFeatures />

      <section className="product-pillars" aria-labelledby="product-pillars-label">
        <h2 id="product-pillars-label" className="visually-hidden">
          How the pipe works
        </h2>
        <ul className="product-pillars__grid">
          <li>
            <strong>HIT</strong>
            <span>Redis replay. Labs silent. Pipe rent on the crossing.</span>
          </li>
          <li>
            <strong>MISS</strong>
            <span>BYOK upstream. Completion stored. Pipe rent still ticks.</span>
          </li>
          <li>
            <strong>Account</strong>
            <span>Email + password login. Intermediate key bound to your profile.</span>
          </li>
          <li>
            <strong>Inventory</strong>
            <span>Tenant-scoped exact-replay tips — never a training corpus.</span>
          </li>
        </ul>
      </section>

      <section className="product-more" aria-labelledby="product-more-label">
        <h2 id="product-more-label" className="board__label">
          Go deeper
        </h2>
        <ul className="board__grid marketing-index">
          {deepLinks.map((item) => (
            <li key={item.slug}>
              <Link href={`/product/${item.slug}`} className="card card--tap">
                {item.eyebrow ? (
                  <p className="card__eyebrow">{item.eyebrow}</p>
                ) : null}
                <h3 className="card__title">{item.title}</h3>
                <p className="card__desc">{item.description}</p>
                <span className="card__go" aria-hidden="true">
                  Open →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
