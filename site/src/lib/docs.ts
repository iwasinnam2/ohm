import fs from "node:fs";
import path from "node:path";

export type DocMeta = {
  slug: string;
  title: string;
  description: string;
};

export type DocGroup = {
  id: string;
  title: string;
  docs: DocMeta[];
};

/** Curated docs — groups drive the docs index + sidebar. */
export const DOC_GROUPS: DocGroup[] = [
  {
    id: "start",
    title: "Start",
    docs: [
      {
        slug: "quickstart",
        title: "Quickstart",
        description: "One base URL, BYOK, seat — Agent Shell or any OpenAI client.",
      },
      {
        slug: "examples",
        title: "Drop-in examples",
        description: "OpenAI-compatible API — no new protocol.",
      },
      {
        slug: "pricing",
        title: "Pricing",
        description: "Seat + meters — pipe rent, not token wholesale.",
      },
    ],
  },
  {
    id: "operative",
    title: "Operative",
    docs: [
      {
        slug: "optimized-usage",
        title: "Optimized usage",
        description: "Cache-first prompting, fetch with intent, read your meters.",
      },
      {
        slug: "streaming",
        title: "Streaming & failover",
        description: "SSE pass-through, failover scope, mid-stream limits.",
      },
      {
        slug: "commands",
        title: "Command catalog",
        description: "MCP tools and skills — what agents can call.",
      },
      {
        slug: "status",
        title: "Status & limits",
        description: "Rate limits, hosts, and edge availability.",
      },
    ],
  },
  {
    id: "connect",
    title: "Connect",
    docs: [
      {
        slug: "integrations",
        title: "Integrations",
        description:
          "Brand board — Cursor, Claude, VS Code, Windsurf, Zed, and the pipe stack.",
      },
      {
        slug: "cursor",
        title: "Cursor / MCP",
        description: "One-click MCP attach and manual mcp.json for Cursor.",
      },
    ],
  },
  {
    id: "admin",
    title: "Admin",
    docs: [
      {
        slug: "enterprise-chaos",
        title: "Enterprise chaos",
        description:
          "How withOhm governs shadow AI, repeat spend, browse risk, and FinOps.",
      },
      {
        slug: "security",
        title: "Security",
        description: "What is cached, retention, keys, and headers.",
      },
      {
        slug: "brand",
        title: "Brand",
        description: "withOhm naming and deferred sk-at / X-AT rename.",
      },
    ],
  },
  {
    id: "legal",
    title: "Legal",
    docs: [
      {
        slug: "legal",
        title: "Legal & compliance",
        description: "Public-only web retrieval and ack requirements.",
      },
      {
        slug: "terms",
        title: "Terms of Service",
        description: "tos-2026-07-26 — binds on terms_ack.",
      },
      {
        slug: "privacy",
        title: "Privacy Policy",
        description: "Roles, cache, subprocessors, and contact.",
      },
      {
        slug: "dpa",
        title: "Data Processing Addendum",
        description: "dpa-2026-07-26 — binds on dpa_ack.",
      },
    ],
  },
];

/** Flat index (order = group order, then within-group). */
export const DOC_INDEX: DocMeta[] = DOC_GROUPS.flatMap((g) => g.docs);

const CONTENT_DIR = path.join(process.cwd(), "content", "docs");

export function getDocSlugs(): string[] {
  return DOC_INDEX.map((d) => d.slug);
}

export function getDocMeta(slug: string): DocMeta | undefined {
  return DOC_INDEX.find((d) => d.slug === slug);
}

export function readDocMarkdown(slug: string): string {
  const filePath = path.join(CONTENT_DIR, `${slug}.md`);
  return fs.readFileSync(filePath, "utf8");
}
