/** Graphite tube network + sparse purple payloads (background only).
 *
 * Tubes only — no joint spheres. Tracks claim clear lanes across the
 * viewBox so the mesh breathes. Payloads use paced motion (constant
 * path speed) with soft opacity ramps; one rider per tube.
 */

type Track = {
  d: string;
  dur: string;
  delay: string;
  soft?: boolean;
};

/**
 * Spacious orthographic mesh — viewBox 1200×800.
 * Horizontal belts on distinct Y bands; verticals on distinct X columns.
 * Soft runs sit at the far edges only.
 */
const TRACKS: readonly Track[] = [
  // Upper belt — left → right, steps down once mid-canvas
  {
    d: "M -80 110 H 640 Q 700 110 700 170 V 260 Q 700 320 760 320 H 1280",
    dur: "30s",
    delay: "0s",
  },
  // Mid belt — right → left, steps down once
  {
    d: "M 1280 400 H 560 Q 500 400 500 460 V 540 Q 500 600 440 600 H -80",
    dur: "32s",
    delay: "5s",
  },
  // Lower belt — left → right, steps up once
  {
    d: "M -80 720 H 520 Q 580 720 580 660 V 580 Q 580 520 640 520 H 1280",
    dur: "34s",
    delay: "10s",
  },
  // Left column — top → bottom, jogs right once
  {
    d: "M 180 -60 V 240 Q 180 300 240 300 H 380 Q 440 300 440 360 V 860",
    dur: "28s",
    delay: "2.5s",
  },
  // Right column — bottom → top, jogs left once
  {
    d: "M 1020 860 V 480 Q 1020 420 960 420 H 820 Q 760 420 760 360 V -60",
    dur: "29s",
    delay: "7.5s",
  },
  // Center spine — top → bottom, wide mid jog (claims the open middle)
  {
    d: "M 600 -60 V 200 Q 600 260 520 260 H 300 Q 240 260 240 320 V 860",
    dur: "31s",
    delay: "13s",
  },
  // Far-left soft riser — bottom → top (edge only)
  {
    d: "M 48 860 V 420 Q 48 360 110 360 H 260 Q 320 360 320 300 V -60",
    dur: "38s",
    delay: "16s",
    soft: true,
  },
  // Far-right soft drop — top → bottom (edge only)
  {
    d: "M 1152 -60 V 280 Q 1152 340 1090 340 H 920 Q 860 340 860 400 V 860",
    dur: "40s",
    delay: "9s",
    soft: true,
  },
] as const;

/** Soft fade in/out only — motion itself is paced (no keyPoints remapping). */
const PAYLOAD_OPACITY_TIMES = "0;0.08;0.92;1";
const PAYLOAD_OPACITY = "0;0.88;0.88;0";

export function PipeNetwork() {
  return (
    <div className="pipe-network" aria-hidden="true">
      <svg
        className="pipe-network__svg"
        viewBox="0 0 1200 800"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          {TRACKS.map((track, i) => (
            <path key={`def-${i}`} id={`pipe-track-${i}`} d={track.d} />
          ))}
        </defs>

        {TRACKS.map((track) => (
          <path
            key={track.d}
            className={
              track.soft
                ? "pipe-network__run pipe-network__run--soft"
                : "pipe-network__run"
            }
            d={track.d}
          />
        ))}

        {TRACKS.map((track, i) => (
          <ellipse
            key={`payload-${i}`}
            className="pipe-network__payload"
            rx={5.5}
            ry={2.1}
            cx={0}
            cy={0}
          >
            <animateMotion
              dur={track.dur}
              begin={track.delay}
              repeatCount="indefinite"
              rotate="auto"
              calcMode="paced"
            >
              <mpath href={`#pipe-track-${i}`} />
            </animateMotion>
            <animate
              attributeName="opacity"
              values={PAYLOAD_OPACITY}
              keyTimes={PAYLOAD_OPACITY_TIMES}
              calcMode="spline"
              keySplines="0.4 0 0.2 1;0 0 1 1;0.4 0 0.2 1"
              dur={track.dur}
              begin={track.delay}
              repeatCount="indefinite"
            />
          </ellipse>
        ))}
      </svg>
    </div>
  );
}
