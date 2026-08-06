/** Homepage dual-container aid — Ephemeral Side × Pipeline System. */

export function DualCrossingAid() {
  return (
    <section className="dual-aid" aria-labelledby="dual-aid-label">
      <h2 id="dual-aid-label" className="visually-hidden">
        One crossing. Two kinds of truth.
      </h2>
      <div className="dual-aid__grid">
        <article className="dual-aid__panel dual-aid__panel--ephemeral">
          <h3>Ephemeral Side</h3>
          <p>
            Hot exact-replay: edge HITs, cache trees, content-addressed blobs,
            request context, and BYOK.
          </p>
        </article>
        <div className="dual-aid__crossing" aria-hidden="true">
          <div className="dual-aid__bar" />
          <span>HIT / MISS · metered</span>
        </div>
        <article className="dual-aid__panel dual-aid__panel--durable">
          <h3>Pipeline System</h3>
          <p>
            Durable governance: identity, meters to ledger to Stripe, compliance
            ingest, provider routes, receipts, policy, audit, and FinOps.
          </p>
        </article>
      </div>
    </section>
  );
}
