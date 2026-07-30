import type { MetadataRoute } from "next";
import { DOC_INDEX } from "@/lib/docs";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://www.withohm.dev";
  const now = new Date();
  // Billing sub-pages are disallowed in robots.ts and edge-pending is
  // noindex — neither belongs in the sitemap.
  const staticRoutes = [
    "",
    "/subscriptions",
    "/docs",
    "/status",
  ].map(
    (path) => ({
      url: `${base}${path || "/"}`,
      lastModified: now,
      changeFrequency: "weekly" as const,
      priority: path === "" ? 1 : 0.7,
    }),
  );
  const docs = DOC_INDEX.map((d) => ({
    url: `${base}/docs/${d.slug}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));
  return [...staticRoutes, ...docs];
}
