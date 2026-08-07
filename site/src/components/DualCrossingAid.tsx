/** Product dual-container aid — Ephemeral Side × Pipeline System. */

type Props = {
  /** Richer motion + denser copy for the Product landing. */
  flashy?: boolean;
};

export function DualCrossingAid({ flashy = false }: Props) {
  return (
    <section
      className={flashy ? "dual-aid dual-aid--flashy" : "dual-aid"}
      aria-labelledby="dual-aid-label"
    >
      <h2 id="dual-aid-label" className={flashy ? "dual-aid__title" : "visually-hidden"}>
        One crossing. Two layers of truth.
      </h2>
      {flashy ? (
        <p className="dual-aid__lede">
          Clients hit one OpenAI-compatible ingress. Replay lives in the
          ephemeral layer; money, policy, and compliance live in the pipeline.
          They meet at <strong>HIT</strong> or <strong>MISS</strong> — always
          metered.
        </p>
      ) : null}
      <div className="dual-aid__grid">
        <article className="dual-aid__panel dual-aid__panel--ephemeral">
          <p className="dual-aid__kicker">Ephemeral layer</p>
          <h3>Exact-replay inventory</h3>
          <ul className="dual-aid__list">
            <li>Edge Redis GET</li>
            <li>Content-addressed blobs</li>
            <li>Cache trees / tips</li>
            <li>BYOK on the wire — never stored</li>
          </ul>
          <p>
            Optimized for latency and mechanical repeat. Can TTL or tear down
            without losing the durable ledger.
          </p>
        </article>
        <div className="dual-aid__crossing" aria-hidden="true">
          <div className="dual-aid__pulse" />
          <div className="dual-aid__bar" />
          <span>HIT / MISS · pipe rent</span>
        </div>
        <article className="dual-aid__panel dual-aid__panel--durable">
          <p className="dual-aid__kicker">Pipeline governance</p>
          <h3>Who may cross</h3>
          <ul className="dual-aid__list">
            <li>Email account + tenant keys</li>
            <li>Meters → ledger → Stripe</li>
            <li>Compliance ingest</li>
            <li>Provider route honesty</li>
          </ul>
          <p>
            Durable governance: tenancy, spend caps, audit, FinOps. Billing
            truth always lives here — even when the edge serves a HIT.
          </p>
        </article>
      </div>
    </section>
  );
}
