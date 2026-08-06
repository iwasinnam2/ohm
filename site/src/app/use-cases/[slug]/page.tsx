import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import { ComposeCiFlowchart } from "@/components/ComposeCiFlowchart";
import { CrossingFlowchart } from "@/components/CrossingFlowchart";
import {
  MarketingArticle,
  type ArticleEmbed,
} from "@/components/MarketingArticle";
import { NoisyNeighborFlowchart } from "@/components/NoisyNeighborFlowchart";
import {
  getUseCaseMeta,
  getUseCaseSlugs,
  readUseCaseMarkdown,
} from "@/lib/useCases";

const CACHE_TREES_MARK = "<!-- ohm:cache-trees-flowchart -->";
const CROSSING_MARK = "<!-- ohm:crossing -->";
const NOISY_MARK = "<!-- ohm:noisy-neighbor -->";
const COMPOSE_MARK = "<!-- ohm:compose-ci -->";

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

function embedsFor(source: string): ArticleEmbed[] {
  const embeds: ArticleEmbed[] = [];
  if (source.includes(CACHE_TREES_MARK)) {
    embeds.push({ mark: CACHE_TREES_MARK, node: <CacheTreesFlowchart /> });
  }
  if (source.includes(NOISY_MARK)) {
    embeds.push({ mark: NOISY_MARK, node: <NoisyNeighborFlowchart /> });
  }
  if (source.includes(CROSSING_MARK)) {
    embeds.push({ mark: CROSSING_MARK, node: <CrossingFlowchart /> });
  }
  if (source.includes(COMPOSE_MARK)) {
    embeds.push({ mark: COMPOSE_MARK, node: <ComposeCiFlowchart /> });
  }
  return embeds;
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

  return (
    <MarketingArticle
      eyebrow={meta.eyebrow ?? "Solutions"}
      title={meta.title}
      description={meta.description}
      source={source}
      embeds={embedsFor(source)}
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
