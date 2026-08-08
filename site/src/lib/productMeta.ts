export type ProductMeta = {
  slug: string;
  title: string;
  description: string;
  eyebrow?: string;
};

/** Product pages — withOhm nouns. */
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
      "Branch exact-replay inventory for PRs and agents — fork, promote, freeze without cloning a database.",
    eyebrow: "Branching",
  },
  {
    slug: "architecture",
    title: "Architecture",
    description:
      "Ephemeral replay × pipeline governance — one metered HIT/MISS crossing.",
    eyebrow: "Deep dive",
  },
  {
    slug: "locality",
    title: "Locality & edge",
    description:
      "Redis edge reads, streamed SSE with pre-first-byte failover, and HIT locality under spiky agent load.",
    eyebrow: "Scale",
  },
  {
    slug: "what-is-withohm",
    title: "What is withOhm",
    description:
      "AI traffic utility — metered pipe on wasted and repeated inference.",
    eyebrow: "Position",
  },
  {
    slug: "trust",
    title: "Trust",
    description:
      "Prove the pipe yourself — waste demo, meters, savings, and account custody. No marketing theatre.",
    eyebrow: "Proof",
  },
];
