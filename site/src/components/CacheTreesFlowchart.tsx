/** Cache trees flowchart — Neon-grammar labels, quiet panels, promote bridge. */

export function CacheTreesFlowchart() {
  return (
    <figure className="ohm-flow" aria-labelledby="ohm-flow-cache-trees-title">
      <figcaption id="ohm-flow-cache-trees-title" className="ohm-flow__title">
        withOhm cache trees
      </figcaption>
      <svg
        className="ohm-flow__svg"
        viewBox="0 0 720 280"
        role="img"
        aria-label="Preview inventory promotes into main inventory; preview can read from main"
      >
        <defs>
          <pattern
            id="ohm-hatch"
            width="8"
            height="8"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <line
              x1="0"
              y1="0"
              x2="0"
              y2="8"
              stroke="rgba(242,235,224,0.12)"
              strokeWidth="1"
            />
          </pattern>
        </defs>

        {/* Callouts */}
        <g className="ohm-flow__callout">
          <rect x="48" y="18" width="128" height="28" rx="14" />
          <text x="112" y="36" textAnchor="middle">
            Branch for a PR
          </text>
          <line x1="112" y1="46" x2="112" y2="72" />
        </g>
        <g className="ohm-flow__callout">
          <rect x="268" y="18" width="184" height="28" rx="14" />
          <text x="360" y="36" textAnchor="middle">
            Share answers without copying
          </text>
          <line x1="360" y1="46" x2="360" y2="100" />
        </g>
        <g className="ohm-flow__callout">
          <rect x="520" y="18" width="140" height="28" rx="14" />
          <text x="590" y="36" textAnchor="middle">
            Bring hits to main
          </text>
          <line x1="590" y1="46" x2="590" y2="72" />
        </g>

        {/* Preview — dashed ephemeral */}
        <rect
          className="ohm-flow__panel ohm-flow__panel--ephemeral"
          x="40"
          y="72"
          width="200"
          height="100"
          rx="12"
        />
        <text className="ohm-flow__panel-label" x="140" y="128" textAnchor="middle">
          Preview inventory
        </text>

        {/* Main — solid + hatch durable */}
        <rect
          className="ohm-flow__panel ohm-flow__panel--durable"
          x="480"
          y="72"
          width="200"
          height="100"
          rx="12"
        />
        <rect
          x="480"
          y="72"
          width="200"
          height="100"
          rx="12"
          fill="url(#ohm-hatch)"
          pointerEvents="none"
        />
        <text className="ohm-flow__panel-label" x="580" y="128" textAnchor="middle">
          Main inventory
        </text>

        {/* Promote bridge */}
        <path
          className="ohm-flow__promote"
          d="M 240 122 H 300 Q 360 122 360 100 Q 360 78 420 78 H 480"
          fill="none"
        />
        <rect className="ohm-flow__promote-pill" x="318" y="88" width="84" height="28" rx="14" />
        <text className="ohm-flow__promote-text" x="360" y="107" textAnchor="middle">
          Promote
        </text>

        {/* COW read from main */}
        <path
          className="ohm-flow__cow"
          d="M 480 200 H 240"
          fill="none"
          markerEnd="url(#ohm-arrow)"
        />
        <defs>
          <marker
            id="ohm-arrow"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="rgba(242,235,224,0.55)" />
          </marker>
        </defs>
        <g className="ohm-flow__callout">
          <rect x="300" y="212" width="120" height="28" rx="14" />
          <text x="360" y="230" textAnchor="middle">
            Read from main
          </text>
          <line x1="360" y1="212" x2="360" y2="200" />
        </g>
      </svg>
      <p className="ohm-flow__note">
        withOhm branches exact-replay inventory by tip. For pairing tips with a
        database preview branch in CI, see Compose with Neon.
      </p>
    </figure>
  );
}
