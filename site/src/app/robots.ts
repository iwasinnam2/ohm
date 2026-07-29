import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/billing/"],
    },
    sitemap: "https://withohm.dev/sitemap.xml",
    host: "https://withohm.dev",
  };
}
