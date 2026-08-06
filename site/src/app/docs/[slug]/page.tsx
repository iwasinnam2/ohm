import Link from "next/link";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { DocsMarkdown } from "@/components/DocsMarkdown";
import { IntegrationBrandBoard } from "@/components/IntegrationBrandBoard";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import {
  DOC_GROUPS,
  getDocMeta,
  getDocSlugs,
  readDocMarkdown,
} from "@/lib/docs";

const CACHE_TREES_FLOW_MARK = "<!-- ohm:cache-trees-flowchart -->";

type Props = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getDocSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const meta = getDocMeta(slug);
  if (!meta) return { title: "Docs" };
  return { title: meta.title, description: meta.description };
}

export default async function DocPage({ params }: Props) {
  const { slug } = await params;
  const meta = getDocMeta(slug);
  if (!meta) notFound();

  let source: string;
  try {
    source = readDocMarkdown(slug);
  } catch {
    notFound();
  }

  const cleaned = source.replaceAll(CACHE_TREES_FLOW_MARK, "\n");

  const sectionMedia: Record<string, ReactNode> | undefined =
    slug === "cache-trees"
      ? { "": <CacheTreesFlowchart /> }
      : undefined;

  return (
    <div className="doc-layout">
      <aside className="doc-nav" aria-label="Docs">
        <Link href="/docs" className="doc-nav__all">
          All docs
        </Link>
        {DOC_GROUPS.map((group) => (
          <div key={group.id} className="doc-nav__group">
            <p className="doc-nav__group-title">{group.title}</p>
            {group.docs.map((doc) => (
              <Link
                key={doc.slug}
                href={`/docs/${doc.slug}`}
                aria-current={doc.slug === slug ? "page" : undefined}
              >
                {doc.title}
              </Link>
            ))}
          </div>
        ))}
      </aside>
      <div className="doc-body">
        {slug === "integrations" ? (
          <IntegrationBrandBoard showIntro />
        ) : null}
        <DocsMarkdown source={cleaned} sectionMedia={sectionMedia} />
      </div>
    </div>
  );
}
