/** Graphite pipe tracks + small sporadic payloads (background only).
 *
 * Payloads stay lit for most of each path (opacity holds until ~90%), so they
 * travel the full screen — not a third. Tracks span the viewBox edges with
 * balanced left- and right-origin traffic so the mesh is not center-heavy.
 */

type Track = {
  d: string;
  dur: string;
  delay: string;
  /** Soft (thinner) run drawn behind primary tracks */
  soft?: boolean;
};

/** Primary network — full-bleed orthographic runs */
const TRACKS: readonly Track[] = [
  // Left → right (upper)
  {
    d: "M -80 90 H 340 Q 390 90 390 150 V 280 Q 390 330 450 330 H 1180",
    dur: "22s",
    delay: "0.3s",
  },
  // Right → left (upper-mid) — alternate side
  {
    d: "M 1180 160 H 760 Q 700 160 700 220 V 380 Q 700 430 640 430 H -80",
    dur: "24s",
    delay: "2.8s",
  },
  // Left → right (mid)
  {
    d: "M -80 360 H 260 Q 320 360 320 420 V 560 Q 320 610 380 610 H 1180",
    dur: "20s",
    delay: "5.5s",
  },
  // Right → left (lower) — alternate side
  {
    d: "M 1180 520 H 820 Q 760 520 760 460 V 300 Q 760 250 700 250 H -80",
    dur: "26s",
    delay: "1.2s",
  },
  // Top → bottom (left third)
  {
    d: "M 140 -60 V 200 Q 140 260 200 260 H 420 Q 480 260 480 320 V 780",
    dur: "21s",
    delay: "4.0s",
  },
  // Top → bottom (right third) — alternate side
  {
    d: "M 960 -60 V 180 Q 960 240 900 240 H 620 Q 560 240 560 300 V 780",
    dur: "23s",
    delay: "7.6s",
  },
  // Bottom → top (far left edge)
  {
    d: "M 40 780 V 480 Q 40 420 100 420 H 300 Q 360 420 360 360 V -60",
    dur: "25s",
    delay: "9.2s",
  },
  // Bottom → top (far right edge) — alternate side
  {
    d: "M 1060 780 V 500 Q 1060 440 1000 440 H 780 Q 720 440 720 380 V -60",
    dur: "19s",
    delay: "3.6s",
  },
  // Left → right (low belt, soft)
  {
    d: "M -80 660 H 480 Q 540 660 540 600 V 480 Q 540 430 600 430 H 1180",
    dur: "27s",
    delay: "11.4s",
    soft: true,
  },
  // Right → left (high belt, soft) — alternate side
  {
    d: "M 1180 40 H 620 Q 560 40 560 100 V 220 Q 560 270 500 270 H -80",
    dur: "28s",
    delay: "6.1s",
    soft: true,
  },
] as const;

/** Extra payload riders — prefer alternate-side tracks so origins stay mixed */
const EXTRA: readonly Track[] = [
  { d: TRACKS[1].d, dur: "30s", delay: "12.0s" }, // right→left
  { d: TRACKS[3].d, dur: "29s", delay: "8.4s" }, // right→left
  { d: TRACKS[5].d, dur: "31s", delay: "14.2s" }, // right third vertical
  { d: TRACKS[7].d, dur: "27s", delay: "0.9s" }, // far right up
  { d: TRACKS[0].d, dur: "32s", delay: "16.5s" }, // left→right (lighter share)
  { d: TRACKS[9].d, dur: "33s", delay: "10.8s" }, // right→left soft
] as const;

const JOINTS = [
  [390, 90],
  [390, 150],
  [450, 330],
  [700, 160],
  [700, 220],
  [640, 430],
  [320, 360],
  [320, 420],
  [380, 610],
  [760, 520],
  [760, 460],
  [700, 250],
  [140, 200],
  [200, 260],
  [480, 260],
  [480, 320],
  [960, 180],
  [900, 240],
  [560, 240],
  [560, 300],
  [40, 480],
  [100, 420],
  [300, 420],
  [360, 360],
  [1060, 500],
  [1000, 440],
  [780, 440],
  [720, 380],
  [540, 660],
  [540, 600],
  [600, 430],
  [560, 40],
  [560, 100],
  [500, 270],
] as const;

/** Opacity + motion: visible across ~90% of the path (was fading by 28%). */
const PAYLOAD_KEY_TIMES = "0;0.03;0.12;0.88;0.96;1";
const PAYLOAD_KEY_POINTS = "0;0.03;0.12;0.88;0.96;1";
const PAYLOAD_OPACITY = "0;0.85;0.9;0.75;0;0";

export function PipeNetwork() {
  const payloads = [...TRACKS, ...EXTRA];

  return (
    <div className="pipe-network" aria-hidden="true">
      <svg
        className="pipe-network__svg"
        viewBox="0 0 1100 720"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          {payloads.map((track, i) => (
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
        {JOINTS.map(([x, y], i) => (
          <circle
            key={`${x}-${y}-${i}`}
            className="pipe-network__joint"
            cx={x}
            cy={y}
            r={10}
          />
        ))}
        {payloads.map((track, i) => (
          <circle
            key={`payload-${i}`}
            className="pipe-network__payload-dot"
            r={2.2}
            cx={0}
            cy={0}
          >
            <animateMotion
              dur={track.dur}
              begin={track.delay}
              repeatCount="indefinite"
              rotate="0"
              keyTimes={PAYLOAD_KEY_TIMES}
              keyPoints={PAYLOAD_KEY_POINTS}
              calcMode="linear"
            >
              <mpath href={`#pipe-track-${i}`} />
            </animateMotion>
            <animate
              attributeName="opacity"
              values={PAYLOAD_OPACITY}
              keyTimes={PAYLOAD_KEY_TIMES}
              dur={track.dur}
              begin={track.delay}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
    </div>
  );
}
