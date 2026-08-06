import Link from "next/link";
import type { ReactNode } from "react";
import { Markdown } from "@/components/Markdown";

type Cta = {
  href: string;
  label: string;
  primary?: boolean;
};

export type ArticleEmbed = {
  mark: string;
  node: ReactNode;
};

type Props = {
  eyebrow: string;
  title: string;
  description: string;
  source: string;
  /** @deprecated Prefer `embeds` for multiple markers. */
  embed?: ReactNode;
  /** @deprecated Prefer `embeds`. */
  embedMark?: string;
  embeds?: ArticleEmbed[];
  ctas?: Cta[];
  backHref: string;
  backLabel: string;
};

type Segment =
  | { kind: "md"; source: string }
  | { kind: "embed"; node: ReactNode; key: string };

/** Drop YAML frontmatter so it is not rendered as prose. */
function stripFrontmatter(source: string): string {
  if (!source.startsWith("---")) return source;
  const end = source.indexOf("\n---", 3);
  if (end === -1) return source;
  return source.slice(end + 4).replace(/^\s*\n/, "");
}

function buildSegments(
  raw: string,
  embeds: ArticleEmbed[],
): Segment[] {
  const source = stripFrontmatter(raw);
  const active = embeds.filter((e) => e.mark && source.includes(e.mark));
  if (active.length === 0) {
    return [{ kind: "md", source }];
  }

  const segments: Segment[] = [];
  let rest = source;
  let embedIdx = 0;
  while (rest.length > 0) {
    let nextIdx = -1;
    let next: ArticleEmbed | null = null;
    for (const e of active) {
      const i = rest.indexOf(e.mark);
      if (i !== -1 && (nextIdx === -1 || i < nextIdx)) {
        nextIdx = i;
        next = e;
      }
    }
    if (nextIdx === -1 || !next) {
      segments.push({ kind: "md", source: rest });
      break;
    }
    if (nextIdx > 0) {
      segments.push({ kind: "md", source: rest.slice(0, nextIdx) });
    }
    segments.push({
      kind: "embed",
      node: next.node,
      key: `embed-${embedIdx++}-${next.mark}`,
    });
    rest = rest.slice(nextIdx + next.mark.length);
  }
  return segments;
}

export function MarketingArticle({
  eyebrow,
  title,
  description,
  source,
  embed,
  embedMark,
  embeds,
  ctas,
  backHref,
  backLabel,
}: Props) {
  const resolvedEmbeds: ArticleEmbed[] =
    embeds ??
    (embed && embedMark ? [{ mark: embedMark, node: embed }] : []);
  const segments = buildSegments(source, resolvedEmbeds);

  return (
    <article className="marketing-article">
      <header className="page-head marketing-article__head">
        <p className="marketing-article__eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
        {ctas && ctas.length > 0 ? (
          <div className="cta-row marketing-article__cta">
            {ctas.map((cta) => (
              <Link
                key={cta.href + cta.label}
                href={cta.href}
                className={cta.primary ? "btn btn--primary" : "link-quiet"}
              >
                {cta.label}
              </Link>
            ))}
          </div>
        ) : null}
      </header>
      <div className="marketing-article__body">
        {segments.map((seg, i) =>
          seg.kind === "embed" ? (
            <div key={seg.key}>{seg.node}</div>
          ) : (
            <Markdown key={`md-${i}`} source={seg.source} />
          ),
        )}
      </div>
      <p className="marketing-article__back">
        <Link href={backHref}>{backLabel} →</Link>
      </p>
    </article>
  );
}
