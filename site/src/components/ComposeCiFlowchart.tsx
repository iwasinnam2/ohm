/** CI job: Ohm cache tree + optional DB preview peer. Middleware governance. */

export function ComposeCiFlowchart() {
  return (
    <figure className="ohm-flow" aria-labelledby="ohm-flow-compose-title">
      <figcaption id="ohm-flow-compose-title" className="ohm-flow__title">
        withOhm — middleware governance
      </figcaption>
      <svg
        className="ohm-flow__svg"
        viewBox="0 0 720 280"
        role="img"
        aria-label="CI job sets X-Ohm-Cache-Tree and optionally a Neon database preview branch"
      >
        <rect className="ohm-flow__panel" x="260" y="16" width="200" height="40" rx="10" />
        <text className="ohm-flow__panel-label" x="360" y="42" textAnchor="middle">
          CI job · PR 842
        </text>
        <path className="ohm-flow__cow" d="M300 56 V 88" fill="none" />
        <path className="ohm-flow__cow" d="M420 56 V 88" fill="none" />

        <rect className="ohm-flow__panel" x="60" y="88" width="260" height="120" rx="14" />
        <text className="ohm-flow__panel-label" x="190" y="120" textAnchor="middle">
          withOhm
        </text>
        <text className="ohm-flow__caption" x="190" y="140" textAnchor="middle">
          exact-replay inventory
        </text>
        <rect className="ohm-flow__chip" x="90" y="160" width="220" height="28" rx="8" />
        <text className="ohm-flow__chip-text" x="190" y="178" textAnchor="middle">
          X-Ohm-Cache-Tree: pr-842
        </text>

        <rect
          className="ohm-flow__panel ohm-flow__panel--ephemeral"
          x="400"
          y="88"
          width="260"
          height="120"
          rx="14"
        />
        <text className="ohm-flow__panel-label" x="530" y="120" textAnchor="middle">
          Neon preview
        </text>
        <text className="ohm-flow__caption" x="530" y="140" textAnchor="middle">
          DB + AI Gateway beta
        </text>
        <rect className="ohm-flow__chip" x="430" y="160" width="200" height="28" rx="8" />
        <text className="ohm-flow__chip-text" x="530" y="178" textAnchor="middle">
          preview branch · PR 842
        </text>

        <g className="ohm-flow__callout">
          <rect x="160" y="230" width="400" height="32" rx="14" />
          <text x="360" y="250" textAnchor="middle">
            Same slug. Compose peers. Promote on merge.
          </text>
        </g>
      </svg>
      <p className="ohm-flow__note">
        Neon branches state (and, in beta, the model path). withOhm branches
        exact-replay inventory — middleware governance on mechanical repeats.
      </p>
    </figure>
  );
}
