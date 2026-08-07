export type UseCaseMeta = {
  slug: string;
  title: string;
  description: string;
  eyebrow?: string;
};

/** Solutions longforms — Neon /use-cases filetree, Ohm nouns. */
export const USE_CASE_INDEX: UseCaseMeta[] = [
  {
    slug: "inventory-per-tenant",
    title: "Inventory per tenant",
    description:
      "Same model. Same gateway. Separate tips — so agent runs do not collide on main.",
    eyebrow: "Flagship",
  },
  {
    slug: "agents",
    title: "Agents on the pipe",
    description:
      "Mechanical agent traffic through one OpenAI-compatible pipe with BYOK and zero-token replay.",
    eyebrow: "Agents",
  },
  {
    slug: "ci-preview",
    title: "CI preview inventory",
    description:
      "Preview cache trees per PR, promote hits to main, compose with Neon branches in CI.",
    eyebrow: "CI",
  },
  {
    slug: "enterprise-chaos",
    title: "Enterprise chaos",
    description:
      "Govern shadow AI, repeat spend, browse risk, and FinOps on one OpenAI-compatible pipe.",
    eyebrow: "Enterprise",
  },
  {
    slug: "compliant-fetch",
    title: "Compliant public-web fetch",
    description:
      "Public-only retrieval with intent, receipts, and policy — never a training corpus.",
    eyebrow: "Compliance",
  },
  {
    slug: "variable-load",
    title: "Variable load",
    description:
      "Spiky CI and agent suites: edge HIT locality and meters that stay honest under wobble.",
    eyebrow: "Scale",
  },
];
