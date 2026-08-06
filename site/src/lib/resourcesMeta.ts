export type ResourceMeta = {
  slug: string;
  href: string;
  title: string;
  description: string;
  eyebrow?: string;
};

/** Resources spine — Neon Resources mega, Ohm nouns. Blog/case studies deferred. */
export const RESOURCES_INDEX: ResourceMeta[] = [
  {
    slug: "changelog",
    href: "/changelog",
    title: "Changelog",
    description: "Shipped product and site updates — cache trees, Product/Solutions, pricing.",
    eyebrow: "Updates",
  },
  {
    slug: "security",
    href: "/security",
    title: "Security",
    description: "Cache purpose, keys, receipts, honesty map — compliance without theatre.",
    eyebrow: "Trust",
  },
  {
    slug: "contact",
    href: "/contact",
    title: "Contact",
    description: "Enterprise inquiry, design partners, and support paths.",
    eyebrow: "Talk to us",
  },
  {
    slug: "support",
    href: "/support",
    title: "Support",
    description: "Help for Intermediate seats and pipe questions.",
    eyebrow: "Help",
  },
  {
    slug: "docs",
    href: "/docs",
    title: "Docs",
    description: "Quickstart, architecture, API index, legal.",
    eyebrow: "Reference",
  },
];
