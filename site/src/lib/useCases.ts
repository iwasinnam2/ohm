import fs from "node:fs";
import path from "node:path";
import {
  USE_CASE_INDEX,
  type UseCaseMeta,
} from "@/lib/useCasesMeta";

export type { UseCaseMeta };
export { USE_CASE_INDEX };

const CONTENT_DIR = path.join(process.cwd(), "content", "use-cases");

export function getUseCaseSlugs(): string[] {
  return USE_CASE_INDEX.map((u) => u.slug);
}

export function getUseCaseMeta(slug: string): UseCaseMeta | undefined {
  return USE_CASE_INDEX.find((u) => u.slug === slug);
}

export function readUseCaseMarkdown(slug: string): string {
  return fs.readFileSync(path.join(CONTENT_DIR, `${slug}.md`), "utf8");
}
