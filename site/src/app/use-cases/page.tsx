import Link from "next/link";
import type { Metadata } from "next";
import { USE_CASE_INDEX } from "@/lib/useCases";

export const metadata: Metadata = {
  title: "Solutions",
  description:
    "withOhm use cases — agents, CI preview inventory, enterprise chaos, compliant fetch, variable load.",
};

export default function UseCasesIndexPage() {
  return (
    <>
      <header className="page-head">
        <h1>Solutions</h1>
        <p>
          How teams put exact-replay inventory and the governance pipeline to
          work — without confusing Ohm with a database.
        </p>
      </header>
      <ul className="board__grid marketing-index">
        {USE_CASE_INDEX.map((item) => (
          <li key={item.slug}>
            <Link href={`/use-cases/${item.slug}`} className="card card--tap">
              {item.eyebrow ? (
                <p className="card__eyebrow">{item.eyebrow}</p>
              ) : null}
              <h2 className="card__title">{item.title}</h2>
              <p className="card__desc">{item.description}</p>
              <span className="card__go" aria-hidden="true">
                Read →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
