import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Status",
  description: "withOhm service status — docs, API, and limits.",
};

const COMPONENTS = [
  {
    name: "Docs / marketing",
    host: "www.withohm.dev",
    state: "operational",
    detail: "AWS Amplify (WEB_COMPUTE) + CloudFront",
  },
  {
    name: "Public API",
    host: "api.withohm.dev",
    state: "operational",
    detail: "EKS edges + Global Accelerator Anycast",
  },
  {
    name: "Fetch toy",
    host: "fetch.withohm.dev",
    state: "operational",
    detail: "Public demo strip — not the full compliance pipe",
  },
  {
    name: "Local edge (dev)",
    host: "localhost:8081",
    state: "supported",
    detail: "Rust gateway for local smoke — optional for production attach",
  },
] as const;

export default function StatusPage() {
  return (
    <>
      <header className="page-head">
        <h1>Status</h1>
        <p>
          Live component view for withOhm. Also at{" "}
          <code>status.withohm.dev</code>.
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
        <Link href="/docs/status">docs/status</Link>. Privacy:{" "}
        <Link href="/docs/privacy">docs/privacy</Link>.
      </p>
    </>
  );
}
