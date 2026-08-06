/** Partition docs markdown into H2 sections with context-aware copy/media layout. */

export type DocSection = {
  /** Heading text without ##, empty for lead before first H2 */
  title: string;
  copy: string;
  media: string;
  /** When true, render copy|media two-column; otherwise keep reading order inline. */
  twoColumn: boolean;
};

type BlockKind = "prose" | "fence" | "table" | "quote" | "image";

type Block = {
  kind: BlockKind;
  text: string;
};

function isTableSeparator(line: string): boolean {
  return /^\s*\|?[\s|:.-]+\|[\s|:.-]*$/.test(line);
}

function isTableRow(line: string): boolean {
  return line.includes("|") && line.trim() !== "";
}

function isRail(kind: BlockKind): boolean {
  return kind === "fence" || kind === "table" || kind === "image";
}

/** Short header/slug specimens stay with prose; longer samples may sit on a rail. */
function isSpecimenFence(text: string): boolean {
  const inner = text
    .replace(/^\s*```[^\n]*\n?/, "")
    .replace(/\n?```\s*$/, "");
  const nonEmpty = inner.split("\n").filter((l) => l.trim().length > 0).length;
  return nonEmpty > 0 && nonEmpty <= 3;
}

function hasSubstance(block: Block): boolean {
  return block.text.trim().length > 0;
}

/** Tokenize a section body into ordered prose / media blocks. */
export function tokenizeDocBlocks(body: string): Block[] {
  const lines = body.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  let proseBuf: string[] = [];

  const flushProse = () => {
    if (proseBuf.length === 0) return;
    const text = proseBuf.join("\n");
    proseBuf = [];
    if (text.trim().length === 0) return;
    blocks.push({ kind: "prose", text });
  };

  while (i < lines.length) {
    const line = lines[i] ?? "";

    // Fenced code
    if (line.trimStart().startsWith("```")) {
      flushProse();
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
      blocks.push({ kind: "fence", text: buf.join("\n") });
      continue;
    }

    // Blockquote (narrative callout — never a rail candidate)
    if (line.startsWith(">")) {
      flushProse();
      const buf: string[] = [];
      while (i < lines.length) {
        const cur = lines[i] ?? "";
        if (cur.startsWith(">")) {
          buf.push(cur);
          i += 1;
          continue;
        }
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
      blocks.push({ kind: "quote", text: buf.join("\n") });
      continue;
    }

    // GFM table
    if (
      isTableRow(line) &&
      i + 1 < lines.length &&
      isTableSeparator(lines[i + 1] ?? "")
    ) {
      flushProse();
      const buf = [line, lines[i + 1] ?? ""];
      i += 2;
      while (i < lines.length && isTableRow(lines[i] ?? "")) {
        buf.push(lines[i] ?? "");
        i += 1;
      }
      blocks.push({ kind: "table", text: buf.join("\n") });
      continue;
    }

    // Standalone image
    if (/^\s*!\[[^\]]*\]\([^)]+\)\s*$/.test(line)) {
      flushProse();
      blocks.push({ kind: "image", text: line.trim() });
      i += 1;
      continue;
    }

    proseBuf.push(line);
    i += 1;
  }

  flushProse();
  return blocks;
}

function narrativeBlocks(blocks: Block[]): Block[] {
  return blocks.filter(
    (b) => (b.kind === "prose" || b.kind === "quote") && hasSubstance(b),
  );
}

/** Short post-sample captions ("Identical second call → HIT") may sit opposite code. */
function isShortCaption(blocks: Block[]): boolean {
  const text = narrativeBlocks(blocks)
    .map((b) => b.text.trim())
    .join("\n")
    .trim();
  if (!text) return true;
  // One short paragraph / sentence — not a real explanation column.
  const words = text.split(/\s+/).filter(Boolean).length;
  return words > 0 && words <= 24 && !text.includes("\n\n");
}

/**
 * Two-column only for terminal showcases (intro prose → code/table/figure).
 * Keep interleaved specimens, mid-sentence curls, and callouts in reading order.
 */
export function shouldUseTwoColumn(blocks: Block[]): boolean {
  const rails = blocks
    .map((b, index) => ({ b, index }))
    .filter(({ b }) => isRail(b.kind) && hasSubstance(b));

  if (rails.length === 0) return false;

  // Specimen-only fences (headers, slugs) never earn a rail.
  const onlySpecimens = rails.every(
    ({ b }) => b.kind === "fence" && isSpecimenFence(b.text),
  );
  if (onlySpecimens) return false;

  const firstRail = rails[0]!.index;
  const lastRail = rails[rails.length - 1]!.index;
  const before = blocks.slice(0, firstRail);
  const after = blocks.slice(lastRail + 1);

  const narrativeBefore = narrativeBlocks(before).length > 0;
  const narrativeAfter = narrativeBlocks(after).length > 0;

  // Honesty-map pattern: "The live map is:" → curl → "Each non-goal…"
  if (narrativeBefore && narrativeAfter) return false;

  // Media-first with a real explanation after — keep source order (Fence tables).
  if (!narrativeBefore && narrativeAfter && !isShortCaption(after)) {
    return false;
  }

  // Showcase: prose → terminal media, media + short caption, or media-only.
  return true;
}

/**
 * Split a section body into prose (left) and media blocks (right) when
 * context warrants a two-column showcase; otherwise keep source order inline.
 */
export function partitionCopyMedia(body: string): {
  copy: string;
  media: string;
  twoColumn: boolean;
} {
  const blocks = tokenizeDocBlocks(body);
  if (blocks.length === 0) {
    return { copy: "", media: "", twoColumn: false };
  }

  const twoColumn = shouldUseTwoColumn(blocks);

  if (!twoColumn) {
    return {
      copy: blocks
        .map((b) => b.text)
        .join("\n\n")
        .replace(/^\n+/, "")
        .replace(/\n+$/, ""),
      media: "",
      twoColumn: false,
    };
  }

  const copyParts: string[] = [];
  const mediaParts: string[] = [];
  for (const block of blocks) {
    if (isRail(block.kind)) {
      mediaParts.push(block.text);
    } else {
      copyParts.push(block.text);
    }
  }

  return {
    copy: copyParts.join("\n\n").replace(/^\n+/, "").replace(/\n+$/, ""),
    media: mediaParts.join("\n\n").trim(),
    twoColumn: true,
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
      const { copy, media, twoColumn } = partitionCopyMedia(body);
      sections.push({ title, copy, media, twoColumn });
    } else {
      // Lead (H1 + intro)
      const { copy, media, twoColumn } = partitionCopyMedia(trimmed);
      sections.push({ title: "", copy, media, twoColumn });
    }
  }

  return sections;
}
