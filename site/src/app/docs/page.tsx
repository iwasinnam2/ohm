import Link from "next/link";
import type { Metadata } from "next";
import { DOC_INDEX } from "@/lib/docs";

export const metadata: Metadata = {
  title: "Docs",
  description: "Quickstart, streaming, pricing, and security for Ohm.",
};

export default function DocsIndexPage() {
  return (
    <>
      <header className="page-head">
        <h1>Docs</h1>
        <p>
          Point your OpenAI SDK at Ohm. One <code>base_url</code> — cache,
          failover, and a meter you can read.
        </p>
      </header>
      <ul className="doc-list">
        {DOC_INDEX.map((doc) => (
          <li key={doc.slug}>
            <Link href={`/docs/${doc.slug}`}>
              <div>
                <p className="doc-list__title">{doc.title}</p>
                <p className="doc-list__desc">{doc.description}</p>
              </div>
              <span className="doc-list__arrow" aria-hidden="true">
                →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
