import type { ReactNode } from "react";
import { Markdown } from "@/components/Markdown";
import { splitDocSections } from "@/lib/docsLayout";

type Props = {
  source: string;
  /** Optional media inject keyed by ## title; use "" for the lead band. */
  sectionMedia?: Record<string, ReactNode>;
};

export function DocsMarkdown({ source, sectionMedia }: Props) {
  const sections = splitDocSections(source);

  return (
    <div className="docs-article">
      {sections.map((section, i) => {
        const inject = sectionMedia?.[section.title];
        const hasMedia = Boolean(section.media) || Boolean(inject);

        return (
          <section
            key={`${section.title || "lead"}-${i}`}
            className={
              hasMedia
                ? "doc-section"
                : "doc-section doc-section--copy-only"
            }
            aria-labelledby={
              section.title ? `doc-sec-${i}` : undefined
            }
          >
            {section.title ? (
              <h2 className="doc-section__title" id={`doc-sec-${i}`}>
                {section.title}
              </h2>
            ) : null}

            <div className="doc-section__copy">
              {section.copy ? <Markdown source={section.copy} /> : null}
            </div>

            {hasMedia ? (
              <div className="doc-section__media">
                {section.media ? <Markdown source={section.media} /> : null}
                {inject}
              </div>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
