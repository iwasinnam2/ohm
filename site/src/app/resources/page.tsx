import Link from "next/link";
import type { Metadata } from "next";
import { RESOURCES_INDEX } from "@/lib/resourcesMeta";

export const metadata: Metadata = {
  title: "Resources",
  description:
    "withOhm resources — changelog, security, contact, support, and docs.",
};

export default function ResourcesIndexPage() {
  return (
    <>
      <header className="page-head">
        <h1>Resources</h1>
        <p>
          Changelog, security posture, and how to reach us — plus support and
          docs. Case studies and blog come later.
        </p>
      </header>
      <ul className="board__grid marketing-index">
        {RESOURCES_INDEX.map((item) => (
          <li key={item.slug}>
            <Link href={item.href} className="card card--tap">
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
