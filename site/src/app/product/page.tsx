import Link from "next/link";
import type { Metadata } from "next";
import { PRODUCT_INDEX } from "@/lib/product";

export const metadata: Metadata = {
  title: "Product",
  description:
    "withOhm product — OpenAI-compatible pipe, cache trees, architecture, locality, and trust.",
};

export default function ProductIndexPage() {
  return (
    <>
      <header className="page-head">
        <h1>Product</h1>
        <p>
          Exact-replay inventory and a durable governance pipeline — one
          OpenAI-compatible crossing.
        </p>
      </header>
      <ul className="board__grid marketing-index">
        {PRODUCT_INDEX.map((item) => (
          <li key={item.slug}>
            <Link href={`/product/${item.slug}`} className="card card--tap">
              {item.eyebrow ? (
                <p className="card__eyebrow">{item.eyebrow}</p>
              ) : null}
              <h2 className="card__title">{item.title}</h2>
              <p className="card__desc">{item.description}</p>
              <span className="card__go" aria-hidden="true">
                Open →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
