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
        const hasInject = Boolean(inject);
        const hasMarkdownMedia = Boolean(section.media);
        const useTwoColumn =
          hasInject || (section.twoColumn && hasMarkdownMedia);
        const mediaOnly =
          useTwoColumn && !section.copy.trim() && (hasMarkdownMedia || hasInject);

        let sectionClass = "doc-section doc-section--copy-only";
        if (mediaOnly) {
          sectionClass = "doc-section doc-section--media-only";
        } else if (useTwoColumn) {
          sectionClass = "doc-section";
        }

        return (
          <section
            key={`${section.title || "lead"}-${i}`}
            className={sectionClass}
            aria-labelledby={
              section.title ? `doc-sec-${i}` : undefined
            }
          >
            {section.title ? (
              <h2 className="doc-section__title" id={`doc-sec-${i}`}>
                {section.title}
              </h2>
            ) : null}

            {section.copy.trim() ? (
              <div className="doc-section__copy">
                <Markdown source={section.copy} />
              </div>
            ) : null}

            {useTwoColumn ? (
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
