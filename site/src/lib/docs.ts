import fs from "node:fs";
import path from "node:path";

export type DocMeta = {
  slug: string;
  title: string;
  description: string;
};

/** Curated docs surfaced on the marketing site (order = nav order). */
export const DOC_INDEX: DocMeta[] = [
  {
    slug: "quickstart",
    title: "Quickstart",
    description: "base_URL + BYOK — Agent Shell first; MCP optional.",
  },
  {
    slug: "enterprise-chaos",
    title: "Enterprise chaos",
    description: "SSO, clean ledger, org policy, Agent Shell — Cursor optional.",
  },
  {
    slug: "examples",
    title: "Drop-in examples",
    description: "OpenAI-compatible API — no new protocol.",
  },
  {
    slug: "optimized-usage",
    title: "Optimized usage",
    description: "Cache-first prompting, fetch with intent, read your meters.",
  },
  {
    slug: "cursor",
    title: "Cursor / MCP (compatibility)",
    description: "Optional MCP attach — not required to use withOhm.",
  },
  {
    slug: "integrations",
    title: "Integrations (compatibility)",
    description: "MCP hosts: Cursor, Claude Code, VS Code, Windsurf, Zed.",
  },
  {
    slug: "commands",
    title: "Command catalog",
    description: "MCP tools and skills (compatibility surface).",
  },
  {
    slug: "streaming",
    title: "Streaming & failover",
    description: "SSE pass-through, failover scope, mid-stream limits.",
  },
  {
    slug: "pricing",
    title: "Pricing",
    description: "Seat + meters — pipe rent, not token wholesale.",
  },
  {
    slug: "security",
    title: "Security",
    description: "What is cached, retention, keys, and headers.",
  },
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
  {
    slug: "status",
    title: "Status & limits",
    description: "Rate limits, hosts, and edge availability.",
  },
  {
    slug: "brand",
    title: "Brand",
    description: "withOhm naming and deferred sk-at / X-AT rename.",
  },
];

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
