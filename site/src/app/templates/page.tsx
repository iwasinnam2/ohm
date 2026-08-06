import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Templates",
  description:
    "Steal-ready starters — cursor-agent-with-web and Neon × Ohm CI compose.",
  robots: { index: false, follow: false },
};

export default function TemplatesPage() {
  return (
    <>
      <header className="page-head">
        <h1>Steal the template</h1>
        <p>
          Clone → set key → ship. People steal templates. They don’t take
          meetings.
        </p>
      </header>

      <div className="partner">
        <h2 className="partner__name">neon-ohm-ci</h2>
        <p>
          <strong>withOhm — middleware governance</strong> beside Neon AI
          Gateway beta. Same PR slug for the Neon preview branch and the Ohm
          tip; Promote on merge.
        </p>
        <pre className="steal__share">{`git clone https://github.com/iwasinnam2/ohm.git
cd ohm/templates/neon-ohm-ci
# secrets: OHM_API_KEY — see README`}</pre>
        <p className="partner__cta cta-row">
          <a
            className="btn btn--primary"
            href="https://github.com/iwasinnam2/ohm/tree/master/templates/neon-ohm-ci"
          >
            Open on GitHub
          </a>
          <Link className="link-quiet" href="/docs/compose-neon">
            Compose docs
          </Link>
        </p>
      </div>

      <div className="partner">
        <h2 className="partner__name">cursor-agent-with-web</h2>
        <p>
          Compliant fetch for agents via withOhm MCP. Clone → set key → agent
          can fetch docs.
        </p>
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
            href="https://github.com/iwasinnam2/ohm/tree/master/templates/cursor-agent-with-web"
          >
            Open on GitHub
          </a>
          <Link className="link-quiet" href="/i">
            Install line
          </Link>
        </p>
      </div>
    </>
  );
}
