import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Status",
  description: "withOhm service status — docs, API edge, and limits.",
};

const COMPONENTS = [
  {
    name: "Docs / marketing",
    host: "withohm.dev",
    state: "operational",
    detail: "Vercel production",
  },
  {
    name: "Public API",
    host: "api.withohm.dev",
    state: "edge_pending",
    detail: "ACM issued; chat cutover per API_CUTOVER runbook",
  },
  {
    name: "Supported edge",
    host: "localhost:8081",
    state: "supported",
    detail: "Rust gateway — current client entry until public cutover",
  },
] as const;

export default function StatusPage() {
  return (
    <>
      <header className="page-head">
        <h1>Status</h1>
        <p>
          Component view for withOhm. Attach <code>status.withohm.dev</code> as
          a Vercel domain pointing at this page.
        </p>
      </header>
      <ul className="status-list">
        {COMPONENTS.map((c) => (
          <li key={c.host} className="status-list__item">
            <div className="status-list__row">
              <strong>{c.name}</strong>
              <span className={`status-pill status-pill--${c.state}`}>
                {c.state}
              </span>
            </div>
            <code>{c.host}</code>
            <p>{c.detail}</p>
          </li>
        ))}
      </ul>
      <p className="status-foot">
        Limits and compliance caps:{" "}
        <Link href="/docs/status">docs/status</Link>. Cutover:{" "}
        <Link href="/docs/status">API edge notes</Link>.
      </p>
    </>
  );
}
