import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Templates",
  description:
    "Steal cursor-agent-with-web — compliant fetch for agents via withOhm MCP.",
};

export default function TemplatesPage() {
  return (
    <>
      <header className="page-head">
        <h1>Steal the template</h1>
        <p>
          <strong>cursor-agent-with-web</strong> — clone → set key → agent can
          fetch docs. People steal templates. They don’t take meetings.
        </p>
      </header>
      <div className="partner">
        <pre className="steal__share">{`git clone https://github.com/iwasinnam2/ohm.git
cd ohm/templates/cursor-agent-with-web
# then: Add withOhm MCP from https://www.withohm.dev/i`}</pre>
        <p>
          Includes MCP example + skill for <strong>compliant fetch for agents</strong>{" "}
          and an <code>AGENTS.md</code> that points teammates at{" "}
          <Link href="/i">/i</Link>.
        </p>
        <p className="partner__cta cta-row">
          <a
            className="btn btn--primary"
            href="https://github.com/iwasinnam2/ohm/tree/cursor/mesh-phase3-5-prod/templates/cursor-agent-with-web"
          >
            Open on GitHub
          </a>
          <Link className="link-quiet" href="/i">
            Install line
          </Link>
          <Link className="link-quiet" href="/docs/steal-kit">
            Steal-kit / PR pack
          </Link>
        </p>
      </div>
    </>
  );
}
