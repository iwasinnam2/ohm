import type { MetadataRoute } from "next";
import { DOC_INDEX } from "@/lib/docs";
import { PRODUCT_INDEX } from "@/lib/productMeta";
import { USE_CASE_INDEX } from "@/lib/useCasesMeta";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://www.withohm.dev";
  const now = new Date();
  // Billing sub-pages are disallowed in robots.ts and edge-pending is
  // noindex — neither belongs in the sitemap.
  const staticRoutes = [
    "",
    "/subscriptions",
    "/pricing",
    "/product",
    "/use-cases",
    "/resources",
    "/changelog",
    "/security",
    "/contact",
    "/docs",
    "/status",
    "/support",
  ].map((path) => ({
    url: `${base}${path || "/"}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: path === "" ? 1 : 0.7,
  }));
  const docs = DOC_INDEX.map((d) => ({
    url: `${base}/docs/${d.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));
  const product = PRODUCT_INDEX.map((p) => ({
    url: `${base}/product/${p.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.75,
  }));
  const useCases = USE_CASE_INDEX.map((u) => ({
    url: `${base}/use-cases/${u.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.75,
  }));
  return [...staticRoutes, ...product, ...useCases, ...docs];
}
