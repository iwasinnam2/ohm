import type { MetadataRoute } from "next";
import { DOC_INDEX } from "@/lib/docs";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://withohm.dev";
  const now = new Date();
  const staticRoutes = ["", "/design-partners", "/docs", "/status", "/edge-pending"].map(
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
