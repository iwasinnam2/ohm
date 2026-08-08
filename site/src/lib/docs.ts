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
    id: "architecture",
    title: "Architecture",
    docs: [
      {
        slug: "architecture",
        title: "Architecture",
        description:
          "Deep dive — Ephemeral Side × Pipeline System, HIT/MISS paths, and account profiles.",
      },
      {
        slug: "edge",
        title: "Edge & Redis locality",
        description:
          "Why GETs stay close to the work — hot path, key layout, mesh posture.",
      },
      {
        slug: "compose-neon",
        title: "Compose with Neon",
        description:
          "Middleware governance beside Neon AI Gateway beta — same PR slug, tip + Promote.",
      },
      {
        slug: "api",
        title: "API reference",
        description: "Index of public endpoints, headers, and related guides.",
      },
      {
        slug: "receipts",
        title: "Waste demo",
        description: "MISS then HIT proof — pipe rent on both crossings.",
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
        slug: "cache-trees",
        title: "Cache trees",
        description:
          "Branch exact-replay inventory for PRs and agents — tip isolation and Promote.",
      },
      {
        slug: "streaming",
        title: "Streaming & failover",
        description:
          "Pre-first-byte failover (shipped), SSE pass-through, cache replay, mid-stream limits.",
      },
      {
        slug: "commands",
        title: "Command catalog",
        description: "MCP tools and skills — what agents can call.",
      },
      {
        slug: "trust",
        title: "Trust — verify it yourself",
        description: "Waste demo, meters, and public keys for the pipe.",
      },
      {
        slug: "honesty",
        title: "Honesty map",
        description:
          "Every non-goal ships with the endpoint or artifact that proves the limit.",
      },
      {
        slug: "status",
        title: "Status & limits",
        description:
          "Surfaces, hosts, defaults, and compliance gates — the live map.",
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
        description:
          "withOhm promise and value system — the metered pipe on wasted, repeated inference.",
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
      {
        slug: "copyright",
        title: "Copyright & database rights",
        description:
          "copyright-2026-08-07 — excerpt caps, no bulk republication, rights contact.",
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
