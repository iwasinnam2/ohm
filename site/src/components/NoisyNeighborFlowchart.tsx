/** Shared main vs named trees — anti-pattern for inventory isolation. */

export function NoisyNeighborFlowchart() {
  return (
    <figure className="ohm-flow" aria-labelledby="ohm-flow-noisy-title">
      <figcaption id="ohm-flow-noisy-title" className="ohm-flow__title">
        Shared main vs named trees
      </figcaption>
      <svg
        className="ohm-flow__svg"
        viewBox="0 0 720 300"
        role="img"
        aria-label="Left: everyone writes into one main tip. Right: named trees promote into main."
      >
        <defs>
          <pattern
            id="ohm-noisy-hatch"
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
            id="ohm-noisy-bad"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="#e07a6a" />
          </marker>
          <marker
            id="ohm-noisy-ok"
            markerWidth="8"
            markerHeight="8"
            refX="6"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6 Z" fill="#a855f7" />
          </marker>
        </defs>

        <text className="ohm-flow__caption" x="180" y="28" textAnchor="middle">
          One tip for everyone
        </text>
        <text className="ohm-flow__caption" x="540" y="28" textAnchor="middle">
          A tree per stream
        </text>

        <rect
          className="ohm-flow__panel"
          x="60"
          y="48"
          width="240"
          height="200"
          rx="12"
        />
        <rect
          x="100"
          y="100"
          width="160"
          height="72"
          rx="10"
          fill="url(#ohm-noisy-hatch)"
          stroke="rgba(242,235,224,0.55)"
          strokeWidth="1.5"
        />
        <text className="ohm-flow__panel-label" x="180" y="132" textAnchor="middle">
          main tip
        </text>
        <text className="ohm-flow__caption" x="180" y="152" textAnchor="middle">
          everyone writes here
        </text>

        <path
          d="M90 80 H 180"
          fill="none"
          stroke="#e07a6a"
          strokeWidth="2"
          markerEnd="url(#ohm-noisy-bad)"
        />
        <text className="ohm-flow__caption" x="90" y="72">
          CI suite
        </text>
        <path
          d="M270 80 H 180"
          fill="none"
          stroke="#e07a6a"
          strokeWidth="2"
          markerEnd="url(#ohm-noisy-bad)"
        />
        <text className="ohm-flow__caption" x="270" y="72" textAnchor="end">
          agent A
        </text>
        <path
          d="M90 210 H 180"
          fill="none"
          stroke="#e07a6a"
          strokeWidth="2"
          markerEnd="url(#ohm-noisy-bad)"
        />
        <text className="ohm-flow__caption" x="90" y="228">
          agent B
        </text>
        <path
          d="M270 210 H 180"
          fill="none"
          stroke="#e07a6a"
          strokeWidth="2"
          markerEnd="url(#ohm-noisy-bad)"
        />
        <text className="ohm-flow__caption" x="270" y="228" textAnchor="end">
          PR-991
        </text>
        <g className="ohm-flow__callout">
          <rect x="118" y="210" width="124" height="24" rx="12" />
          <text x="180" y="226" textAnchor="middle">
            noisy neighbor
          </text>
        </g>

        <rect
          className="ohm-flow__panel ohm-flow__panel--ephemeral"
          x="420"
          y="48"
          width="240"
          height="200"
          rx="12"
        />
        <rect className="ohm-flow__panel" x="448" y="72" width="88" height="56" rx="8" />
        <text className="ohm-flow__panel-label" x="492" y="98" textAnchor="middle">
          pr-842
        </text>
        <text className="ohm-flow__caption" x="492" y="114" textAnchor="middle">
          suite only
        </text>
        <rect className="ohm-flow__panel" x="544" y="72" width="88" height="56" rx="8" />
        <text className="ohm-flow__panel-label" x="588" y="98" textAnchor="middle">
          agent-a
        </text>
        <text className="ohm-flow__caption" x="588" y="114" textAnchor="middle">
          fleet only
        </text>
        <rect
          className="ohm-flow__panel ohm-flow__panel--durable"
          x="490"
          y="160"
          width="100"
          height="56"
          rx="8"
        />
        <rect
          x="490"
          y="160"
          width="100"
          height="56"
          rx="8"
          fill="url(#ohm-noisy-hatch)"
          pointerEvents="none"
        />
        <text className="ohm-flow__panel-label" x="540" y="186" textAnchor="middle">
          main
        </text>
        <text className="ohm-flow__caption" x="540" y="202" textAnchor="middle">
          promote in
        </text>
        <path
          d="M492 128 V 160"
          fill="none"
          stroke="#a855f7"
          strokeWidth="2.5"
          markerEnd="url(#ohm-noisy-ok)"
        />
        <path
          d="M588 128 V 160"
          fill="none"
          stroke="#a855f7"
          strokeWidth="2.5"
          markerEnd="url(#ohm-noisy-ok)"
        />
        <rect className="ohm-flow__promote-pill" x="508" y="132" width="64" height="20" rx="10" />
        <text className="ohm-flow__promote-text" x="540" y="146" textAnchor="middle">
          Promote
        </text>
      </svg>
      <p className="ohm-flow__note">
        Isolation is a tip problem, not a second gateway problem.
      </p>
    </figure>
  );
}
