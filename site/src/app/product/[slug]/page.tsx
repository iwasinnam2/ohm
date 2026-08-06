import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import { DualCrossingAid } from "@/components/DualCrossingAid";
import { MarketingArticle } from "@/components/MarketingArticle";
import {
  getProductMeta,
  getProductSlugs,
  readProductMarkdown,
} from "@/lib/product";

const CACHE_TREES_MARK = "<!-- ohm:cache-trees-flowchart -->";
const DUAL_MARK = "<!-- ohm:dual-crossing -->";

type Props = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getProductSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const meta = getProductMeta(slug);
  if (!meta) return { title: "Product" };
  return { title: meta.title, description: meta.description };
}

export default async function ProductPage({ params }: Props) {
  const { slug } = await params;
  const meta = getProductMeta(slug);
  if (!meta) notFound();

  let source: string;
  try {
    source = readProductMarkdown(slug);
  } catch {
    notFound();
  }

  const embed =
    slug === "cache-trees" ? (
      <CacheTreesFlowchart />
    ) : slug === "architecture" ? (
      <DualCrossingAid />
    ) : undefined;
  const embedMark =
    slug === "cache-trees"
      ? CACHE_TREES_MARK
      : slug === "architecture"
        ? DUAL_MARK
        : undefined;

  return (
    <MarketingArticle
      eyebrow={meta.eyebrow ?? "Product"}
      title={meta.title}
      description={meta.description}
      source={source}
      embed={embed}
      embedMark={embedMark}
      ctas={[
        {
          href: "/billing/intermediate",
          label: "Start now — $0 seat",
          primary: true,
        },
        { href: "/docs", label: "Docs" },
      ]}
      backHref="/product"
      backLabel="All product"
    />
  );
}
