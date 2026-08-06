import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import { MarketingArticle } from "@/components/MarketingArticle";
import {
  getUseCaseMeta,
  getUseCaseSlugs,
  readUseCaseMarkdown,
} from "@/lib/useCases";

const CACHE_TREES_MARK = "<!-- ohm:cache-trees-flowchart -->";

type Props = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getUseCaseSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const meta = getUseCaseMeta(slug);
  if (!meta) return { title: "Solutions" };
  return { title: meta.title, description: meta.description };
}

export default async function UseCasePage({ params }: Props) {
  const { slug } = await params;
  const meta = getUseCaseMeta(slug);
  if (!meta) notFound();

  let source: string;
  try {
    source = readUseCaseMarkdown(slug);
  } catch {
    notFound();
  }

  const showTrees =
    slug === "inventory-per-tenant" ||
    slug === "ci-preview" ||
    source.includes(CACHE_TREES_MARK);

  return (
    <MarketingArticle
      eyebrow={meta.eyebrow ?? "Solutions"}
      title={meta.title}
      description={meta.description}
      source={source}
      embed={showTrees ? <CacheTreesFlowchart /> : undefined}
      embedMark={showTrees ? CACHE_TREES_MARK : undefined}
      ctas={[
        {
          href: "/billing/intermediate",
          label: "Start now — $0 seat",
          primary: true,
        },
        { href: "/docs/quickstart", label: "Quickstart" },
      ]}
      backHref="/use-cases"
      backLabel="All solutions"
    />
  );
}
