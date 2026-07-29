import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Markdown } from "@/components/Markdown";
import {
  DOC_INDEX,
  getDocMeta,
  getDocSlugs,
  readDocMarkdown,
} from "@/lib/docs";

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
        <Link href="/docs">All docs</Link>
        {DOC_INDEX.map((doc) => (
          <Link
            key={doc.slug}
            href={`/docs/${doc.slug}`}
            aria-current={doc.slug === slug ? "page" : undefined}
          >
            {doc.title}
          </Link>
        ))}
      </aside>
      <Markdown source={source} />
    </div>
  );
}
