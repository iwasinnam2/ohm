/** Graphite pipe tracks + small sporadic payloads (background only). */

const TRACKS = [
  {
    d: "M -40 120 H 280 Q 320 120 320 180 V 420 Q 320 460 360 460 H 980",
    dur: "11s",
    delay: "0.4s",
  },
  {
    d: "M 1100 80 H 720 Q 680 80 680 140 V 360 Q 680 410 640 410 H 180",
    dur: "13s",
    delay: "3.2s",
  },
  {
    d: "M -20 520 H 420 Q 470 520 470 470 V 240 Q 470 190 520 190 H 1200",
    dur: "10s",
    delay: "6.8s",
  },
  {
    d: "M 200 -30 V 200 Q 200 240 250 240 H 700 Q 760 240 760 300 V 640",
    dur: "12s",
    delay: "1.6s",
  },
  {
    d: "M 980 -20 V 160 Q 980 210 920 210 H 540 Q 490 210 490 270 V 700",
    dur: "14s",
    delay: "8.5s",
  },
  {
    d: "M -30 300 H 200 Q 240 300 240 340 V 580 Q 240 620 290 620 H 860",
    dur: "9.5s",
    delay: "5.1s",
  },
] as const;

const EXTRA = [
  { d: TRACKS[0].d, dur: "15s", delay: "7.2s" },
  { d: TRACKS[2].d, dur: "12.5s", delay: "2.4s" },
  { d: TRACKS[4].d, dur: "16s", delay: "10.1s" },
] as const;

const JOINTS = [
  [280, 120],
  [320, 180],
  [360, 460],
  [720, 80],
  [680, 140],
  [640, 410],
  [420, 520],
  [470, 470],
  [520, 190],
  [200, 200],
  [250, 240],
  [700, 240],
  [760, 300],
  [920, 210],
  [490, 270],
  [240, 340],
  [290, 620],
] as const;

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
          <path key={track.d} className="pipe-network__run" d={track.d} />
        ))}
        {JOINTS.map(([x, y], i) => (
          <circle
            key={`${x}-${y}-${i}`}
            className="pipe-network__joint"
            cx={x}
            cy={y}
            r={11}
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
              keyTimes="0;0.04;0.18;0.28;1"
              keyPoints="0;0.04;0.18;0.28;1"
              calcMode="linear"
            >
              <mpath href={`#pipe-track-${i}`} />
            </animateMotion>
            <animate
              attributeName="opacity"
              values="0;0.9;0.7;0;0"
              keyTimes="0;0.04;0.18;0.28;1"
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
