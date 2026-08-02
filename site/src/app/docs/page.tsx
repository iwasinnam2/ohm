import Link from "next/link";
import type { Metadata } from "next";
import { DOC_GROUPS } from "@/lib/docs";

export const metadata: Metadata = {
  title: "Docs",
  description:
    "withOhm docs — Start, Operative, Connect, Admin, and Legal. Interconnectedness and accessibility.",
};

export default function DocsIndexPage() {
  return (
    <>
      <header className="page-head">
        <h1>Docs</h1>
        <p>
          Interconnectedness and accessibility — one <code>base_url</code>, the
          tools you already use, and a meter you can read.
        </p>
      </header>
      {DOC_GROUPS.map((group) => (
        <section
          key={group.id}
          className="doc-group"
          aria-labelledby={`doc-group-${group.id}`}
        >
          <h2 className="doc-group__title" id={`doc-group-${group.id}`}>
            {group.title}
          </h2>
          <ul className="doc-list">
            {group.docs.map((doc) => (
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
        </section>
      ))}
    </>
  );
}
