import fs from "node:fs";
import path from "node:path";
import {
  PRODUCT_INDEX,
  type ProductMeta,
} from "@/lib/productMeta";

export type { ProductMeta };
export { PRODUCT_INDEX };

const CONTENT_DIR = path.join(process.cwd(), "content", "product");

export function getProductSlugs(): string[] {
  return PRODUCT_INDEX.map((p) => p.slug);
}

export function getProductMeta(slug: string): ProductMeta | undefined {
  return PRODUCT_INDEX.find((p) => p.slug === slug);
}

export function readProductMarkdown(slug: string): string {
  return fs.readFileSync(path.join(CONTENT_DIR, `${slug}.md`), "utf8");
}
