import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Markdown } from "@/components/Markdown";
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
        {slug === "cache-trees" && source.includes(CACHE_TREES_FLOW_MARK) ? (
          <>
            <Markdown source={source.split(CACHE_TREES_FLOW_MARK)[0] ?? ""} />
            <CacheTreesFlowchart />
            <Markdown source={source.split(CACHE_TREES_FLOW_MARK)[1] ?? ""} />
          </>
        ) : (
          <Markdown source={source} />
        )}
      </div>
    </div>
  );
}
