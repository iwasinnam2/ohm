import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import { ComposeCiFlowchart } from "@/components/ComposeCiFlowchart";
import { CrossingFlowchart } from "@/components/CrossingFlowchart";
import { DualCrossingAid } from "@/components/DualCrossingAid";
import {
  MarketingArticle,
  type ArticleEmbed,
} from "@/components/MarketingArticle";
import { NoisyNeighborFlowchart } from "@/components/NoisyNeighborFlowchart";
import {
  getProductMeta,
  getProductSlugs,
  readProductMarkdown,
} from "@/lib/product";

const CACHE_TREES_MARK = "<!-- ohm:cache-trees-flowchart -->";
const CACHE_TREES_ALT = "<!-- ohm:cache-trees -->";
const DUAL_MARK = "<!-- ohm:dual-crossing -->";
const CROSSING_MARK = "<!-- ohm:crossing -->";
const NOISY_MARK = "<!-- ohm:noisy-neighbor -->";
const COMPOSE_MARK = "<!-- ohm:compose-ci -->";

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

function embedsFor(slug: string, source: string): ArticleEmbed[] {
  const embeds: ArticleEmbed[] = [];

  if (slug === "cache-trees" || source.includes(CACHE_TREES_MARK)) {
    embeds.push({ mark: CACHE_TREES_MARK, node: <CacheTreesFlowchart /> });
  }
  if (source.includes(CACHE_TREES_ALT)) {
    embeds.push({ mark: CACHE_TREES_ALT, node: <CacheTreesFlowchart /> });
  }
  if (slug === "architecture" && source.includes(DUAL_MARK)) {
    embeds.push({ mark: DUAL_MARK, node: <DualCrossingAid /> });
  }
  if (source.includes(CROSSING_MARK)) {
    embeds.push({ mark: CROSSING_MARK, node: <CrossingFlowchart /> });
  }
  if (source.includes(NOISY_MARK)) {
    embeds.push({ mark: NOISY_MARK, node: <NoisyNeighborFlowchart /> });
  }
  if (source.includes(COMPOSE_MARK)) {
    embeds.push({ mark: COMPOSE_MARK, node: <ComposeCiFlowchart /> });
  }

  return embeds;
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

  return (
    <MarketingArticle
      eyebrow={meta.eyebrow ?? "Product"}
      title={meta.title}
      description={meta.description}
      source={source}
      embeds={embedsFor(slug, source)}
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
