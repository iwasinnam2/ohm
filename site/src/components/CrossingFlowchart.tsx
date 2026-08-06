/** Promote: ephemeral tip → durable main. */

export function CrossingFlowchart() {
  return (
    <figure className="ohm-flow" aria-labelledby="ohm-flow-crossing-title">
      <figcaption id="ohm-flow-crossing-title" className="ohm-flow__title">
        Promote is the only crossing
      </figcaption>
      <svg
        className="ohm-flow__svg"
        viewBox="0 0 720 260"
        role="img"
        aria-label="Ephemeral tip promotes onto durable main"
      >
        <defs>
          <pattern
            id="ohm-cross-hatch"
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
          <marker
            id="ohm-cross-arrow"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="#a855f7" />
          </marker>
        </defs>

        <rect
          className="ohm-flow__panel ohm-flow__panel--ephemeral"
          x="80"
          y="60"
          width="200"
          height="120"
          rx="14"
        />
        <text className="ohm-flow__panel-label" x="180" y="112" textAnchor="middle">
          pr-842
        </text>
        <text className="ohm-flow__caption" x="180" y="136" textAnchor="middle">
          ephemeral tip
        </text>

        <path
          d="M290 120 H 400"
          fill="none"
          stroke="#a855f7"
          strokeWidth="3"
          markerEnd="url(#ohm-cross-arrow)"
        />
        <rect className="ohm-flow__promote-pill" x="318" y="96" width="72" height="24" rx="12" />
        <text className="ohm-flow__promote-text" x="354" y="112" textAnchor="middle">
          Promote
        </text>

        <rect
          className="ohm-flow__panel ohm-flow__panel--durable"
          x="440"
          y="60"
          width="200"
          height="120"
          rx="14"
        />
        <rect
          x="440"
          y="60"
          width="200"
          height="120"
          rx="14"
          fill="url(#ohm-cross-hatch)"
          pointerEvents="none"
        />
        <text className="ohm-flow__panel-label" x="540" y="112" textAnchor="middle">
          main
        </text>
        <text className="ohm-flow__caption" x="540" y="136" textAnchor="middle">
          durable inventory
        </text>

        <text className="ohm-flow__caption" x="360" y="220" textAnchor="middle">
          Dashed = preview tip · Hatch = main · Purple = Promote only
        </text>
      </svg>
      <p className="ohm-flow__note">
        Until Promote, main does not absorb the tip. After Promote, the next job
        on main can hit exact replay for those entries.
      </p>
    </figure>
  );
}
