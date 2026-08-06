import { notFound } from "next/navigation";

/** Public status UI retired — use /docs/status for limits and hosts. */
export default function StatusPage() {
  notFound();
}
