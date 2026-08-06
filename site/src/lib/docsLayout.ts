/** Partition docs markdown into H2 sections with copy (left) vs media (right). */

export type DocSection = {
  /** Heading text without ##, empty for lead before first H2 */
  title: string;
  copy: string;
  media: string;
};

function isTableSeparator(line: string): boolean {
  return /^\s*\|?[\s|:.-]+\|[\s|:.-]*$/.test(line);
}

function isTableRow(line: string): boolean {
  return line.includes("|") && line.trim() !== "";
}

/**
 * Split a section body into prose (left) and media blocks (right):
 * fenced code, GFM tables, blockquotes, standalone images.
 */
export function partitionCopyMedia(body: string): { copy: string; media: string } {
  const lines = body.replace(/\r\n/g, "\n").split("\n");
  const copy: string[] = [];
  const media: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i] ?? "";

    // Fenced code
    if (line.trimStart().startsWith("```")) {
      const buf = [line];
      i += 1;
      while (i < lines.length && !(lines[i] ?? "").trimStart().startsWith("```")) {
        buf.push(lines[i] ?? "");
        i += 1;
      }
      if (i < lines.length) {
        buf.push(lines[i] ?? "");
        i += 1;
      }
      media.push(buf.join("\n"));
      continue;
    }

    // Blockquote (box)
    if (line.startsWith(">")) {
      const buf: string[] = [];
      while (i < lines.length) {
        const cur = lines[i] ?? "";
        if (cur.startsWith(">")) {
          buf.push(cur);
          i += 1;
          continue;
        }
        // allow a single blank inside a quote run if next is still >
        if (
          cur.trim() === "" &&
          i + 1 < lines.length &&
          (lines[i + 1] ?? "").startsWith(">")
        ) {
          buf.push(cur);
          i += 1;
          continue;
        }
        break;
      }
      media.push(buf.join("\n"));
      continue;
    }

    // GFM table
    if (
      isTableRow(line) &&
      i + 1 < lines.length &&
      isTableSeparator(lines[i + 1] ?? "")
    ) {
      const buf = [line, lines[i + 1] ?? ""];
      i += 2;
      while (i < lines.length && isTableRow(lines[i] ?? "")) {
        buf.push(lines[i] ?? "");
        i += 1;
      }
      media.push(buf.join("\n"));
      continue;
    }

    // Standalone image
    if (/^\s*!\[[^\]]*\]\([^)]+\)\s*$/.test(line)) {
      media.push(line.trim());
      i += 1;
      continue;
    }

    copy.push(line);
    i += 1;
  }

  return {
    copy: copy.join("\n").replace(/^\n+/, "").replace(/\n+$/, ""),
    media: media.join("\n\n").trim(),
  };
}

/** Split full docs markdown into lead + ## sections. */
export function splitDocSections(source: string): DocSection[] {
  const normalized = source.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  const parts = normalized.split(/\n(?=## )/);
  const sections: DocSection[] = [];

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith("## ")) {
      const nl = trimmed.indexOf("\n");
      const titleLine = nl === -1 ? trimmed : trimmed.slice(0, nl);
      const body = nl === -1 ? "" : trimmed.slice(nl + 1);
      const title = titleLine.replace(/^##\s+/, "").trim();
      const { copy, media } = partitionCopyMedia(body);
      sections.push({ title, copy, media });
    } else {
      // Lead (H1 + intro) — keep H1 in copy; park any early media on the right
      const { copy, media } = partitionCopyMedia(trimmed);
      sections.push({ title: "", copy, media });
    }
  }

  return sections;
}
