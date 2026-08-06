export type ProductMeta = {
  slug: string;
  title: string;
  description: string;
  eyebrow?: string;
};

/** Product pages — Neon Product mega, Ohm nouns. */
export const PRODUCT_INDEX: ProductMeta[] = [
  {
    slug: "pipe",
    title: "OpenAI-compatible pipe",
    description:
      "One base URL across providers. BYOK, exact-replay meters, compliant fetch on the crossing.",
    eyebrow: "Core",
  },
  {
    slug: "cache-trees",
    title: "Cache trees",
    description:
      "Branch exact-replay inventory for PRs and agents — fork, promote, freeze without cloning Postgres.",
    eyebrow: "Branching",
  },
  {
    slug: "architecture",
    title: "Architecture",
    description:
      "One OpenAI-compatible gateway. Cache tips for inventory. Promote as the only crossing to main.",
    eyebrow: "Deep dive",
  },
  {
    slug: "locality",
    title: "Locality & edge",
    description:
      "Redis edge reads, pre-first-byte failover, and HIT locality under spiky agent load.",
    eyebrow: "Scale",
  },
  {
    slug: "trust",
    title: "Trust & receipts",
    description:
      "Signed cache-hit receipts, public honesty map, JWKS — verify the pipe yourself.",
    eyebrow: "Proof",
  },
  {
    slug: "what-is-withohm",
    title: "What is withOhm",
    description:
      "Tollbooth on wasted inference. Neon branches state; Ohm branches exact replay.",
    eyebrow: "Position",
  },
];
