import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

export default function HomePage() {
  return (
    <section className="hero">
      <div className="hero__lockup">
        <OhmMark className="hero__mark" />
        <h1 className="hero__brand">withOhm</h1>
      </div>
      <p className="hero__promise">
        AI public API model switching, prompt caching and compliant web
        browsing — one OpenAI-compatible pipe. Attach it to Cursor over MCP,
        bring your own provider keys (BYOK), and pay metered rates on a $0
        Intermediate seat.
      </p>
      <div className="hero__cta cta-row">
        <Link href="/subscriptions" className="btn btn--primary">
          Explore subscriptions
        </Link>
        <Link href="/billing/intermediate" className="link-quiet">
          Intermediate ($0 + meters)
        </Link>
        <Link href="/billing/enterprise" className="link-quiet">
          Enterprise application
        </Link>
      </div>
    </section>
  );
}
