import type { Metadata } from "next";
import Link from "next/link";
import { PAYG_RATES, formatUsd } from "@/lib/meterRates";

export const metadata: Metadata = {
  title: "Support",
  description:
    "withOhm support — FAQs on metering, BYOK, cache privacy, and cancellation, plus direct queries to our support inbox.",
};

const FAQS: { q: string; a: React.ReactNode }[] = [
  {
    q: "What is withOhm?",
    a: (
      <>
        <p>
          withOhm is one OpenAI-compatible pipe in front of your existing model
          providers: prompt caching, model switching, and compliant web
          browsing. Point Cursor, Claude Code, VS Code, or any MCP-capable tool
          at it and repeated context becomes cache hits billed at a fraction of
          a fresh provider call. See <Link href="/docs">the docs</Link> for the
          full picture.
        </p>
      </>
    ),
  },
  {
    q: "How does the metering system work?",
    a: (
      <>
        <p>
          The Intermediate seat is <strong>$0/month</strong> — you pay only
          metered rates for what actually flows through the pipe:{" "}
          {formatUsd(PAYG_RATES.cache_hit)} per 1k tokens on cache hits,{" "}
          {formatUsd(PAYG_RATES.cache_miss)} per 1k tokens on cache misses, and{" "}
          {formatUsd(PAYG_RATES.web_fetch)} per web fetch URL. Usage is
          reported to Stripe as it happens and appears itemised on a single
          monthly invoice. The published schedule lives on{" "}
          <Link href="/subscriptions">the subscriptions page</Link>, and you
          can watch your own numbers live with the <code>ohm_usage</code> MCP
          tool.
        </p>
      </>
    ),
  },
  {
    q: "Does withOhm give free access with free API token generation?",
    a: (
      <>
        <p>
          No. withOhm is <strong>BYOK — bring your own keys</strong>. We never
          generate or resell provider tokens; your OpenAI/Anthropic/etc. keys
          stay yours and upstream usage is billed by your provider as normal.
          What withOhm charges for is the pipe itself: a $0 seat plus the
          metered rates above. The savings come from cache hits that stop you
          re-paying your provider for context it has already seen.
        </p>
      </>
    ),
  },
  {
    q: "Is my cached data private?",
    a: (
      <>
        <p>
          Yes. Caches are strictly per-tenant — your workspace&apos;s entries
          are keyed to your tenant and are never shared with, or readable by,
          any other customer. Aggregate statistics (like the public savings
          counter) are anonymous totals with no prompt or completion content.
          Details live in <Link href="/docs/privacy">Privacy</Link> and{" "}
          <Link href="/docs/security">Security</Link>.
        </p>
      </>
    ),
  },
  {
    q: "How do I cancel?",
    a: (
      <>
        <p>
          Any time, self-serve, via the Stripe billing portal linked from your
          checkout confirmation email — cancellation stops future metering
          immediately and your final invoice covers only usage already
          consumed. There is no seat fee to unwind on Intermediate. If
          anything blocks you, <Link href="/support/query">send a query</Link>{" "}
          and a human unblocks you.
        </p>
      </>
    ),
  },
];

export default function SupportPage() {
  return (
    <>
      <header className="page-head">
        <h1>Support</h1>
        <p>
          Answers to the questions we actually get, in plain language. Still
          stuck after reading? Direct queries reach a human inbox — not a bot
          queue.
        </p>
      </header>

      <section className="faq" aria-label="Frequently asked questions">
        {FAQS.map(({ q, a }) => (
          <details key={q} className="faq__item">
            <summary className="faq__q">{q}</summary>
            <div className="faq__a">{a}</div>
          </details>
        ))}
      </section>

      <section className="faq__escalate">
        <p>
          FAQ&apos;s not enough? Don&apos;t hesitate to direct more specific
          questions to our dedicated support at{" "}
          <a href="mailto:queries@withohm.dev">queries@withohm.dev</a>
        </p>
        <Link href="/support/query" className="btn btn--primary">
          Submit a query
        </Link>
      </section>
    </>
  );
}
