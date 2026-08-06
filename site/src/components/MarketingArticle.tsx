import Link from "next/link";
import type { ReactNode } from "react";
import { Markdown } from "@/components/Markdown";

type Cta = {
  href: string;
  label: string;
  primary?: boolean;
};

type Props = {
  eyebrow: string;
  title: string;
  description: string;
  source: string;
  embed?: ReactNode;
  /** Split marker in markdown; embed renders between halves when present. */
  embedMark?: string;
  ctas?: Cta[];
  backHref: string;
  backLabel: string;
};

export function MarketingArticle({
  eyebrow,
  title,
  description,
  source,
  embed,
  embedMark,
  ctas,
  backHref,
  backLabel,
}: Props) {
  const hasEmbed = Boolean(embed && embedMark && source.includes(embedMark));
  const [before, after] = hasEmbed
    ? source.split(embedMark!)
    : [source, ""];

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
        {hasEmbed ? (
          <>
            <Markdown source={before ?? ""} />
            {embed}
            <Markdown source={after ?? ""} />
          </>
        ) : (
          <Markdown source={source} />
        )}
      </div>
      <p className="marketing-article__back">
        <Link href={backHref}>{backLabel} →</Link>
      </p>
    </article>
  );
}
