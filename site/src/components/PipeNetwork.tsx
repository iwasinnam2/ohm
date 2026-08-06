/** Dark graphite tubes + thin purple border rails + sparse purple payloads.
 *
 * Mesh stays nearly silent; only payloads read bright. Accent rails frame
 * the viewport like a sleek page border (left index, top, right).
 */

type Track = {
  d: string;
  dur: string;
  delay: string;
  soft?: boolean;
};

/** Spacious orthographic mesh — viewBox 1200×800. */
const TRACKS: readonly Track[] = [
  {
    d: "M -80 110 H 640 Q 700 110 700 170 V 260 Q 700 320 760 320 H 1280",
    dur: "30s",
    delay: "0s",
  },
  {
    d: "M 1280 400 H 560 Q 500 400 500 460 V 540 Q 500 600 440 600 H -80",
    dur: "32s",
    delay: "5s",
  },
  {
    d: "M -80 720 H 520 Q 580 720 580 660 V 580 Q 580 520 640 520 H 1280",
    dur: "34s",
    delay: "10s",
  },
  {
    d: "M 180 -60 V 240 Q 180 300 240 300 H 380 Q 440 300 440 360 V 860",
    dur: "28s",
    delay: "2.5s",
  },
  {
    d: "M 1020 860 V 480 Q 1020 420 960 420 H 820 Q 760 420 760 360 V -60",
    dur: "29s",
    delay: "7.5s",
  },
  {
    d: "M 600 -60 V 200 Q 600 260 520 260 H 300 Q 240 260 240 320 V 860",
    dur: "31s",
    delay: "13s",
  },
  {
    d: "M 48 860 V 420 Q 48 360 110 360 H 260 Q 320 360 320 300 V -60",
    dur: "38s",
    delay: "16s",
    soft: true,
  },
  {
    d: "M 1152 -60 V 280 Q 1152 340 1090 340 H 920 Q 860 340 860 400 V 860",
    dur: "40s",
    delay: "9s",
    soft: true,
  },
] as const;

/**
 * Thin purple border rails in % viewBox space (preserveAspectRatio=none).
 * Left index + top bridge + right rail — constant accent tubing.
 */
const BORDER_RUNS = [
  // Left index — drops from top, jogs in, runs the full height
  "M 1.6 0 V 8 H 3.4 Q 4.2 8 4.2 10 V 90 Q 4.2 92 3.4 92 H 1.6 V 100",
  // Top rail — left to right under the header edge
  "M 1.6 8 H 98.4",
  // Right rail — mirror of the left index
  "M 98.4 0 V 8 H 96.6 Q 95.8 8 95.8 10 V 90 Q 95.8 92 96.6 92 H 98.4 V 100",
  // Bottom partial — left index foot
  "M 1.6 92 H 18",
  // Bottom partial — right index foot
  "M 82 92 H 98.4",
] as const;

const PAYLOAD_OPACITY_TIMES = "0;0.06;0.94;1";
const PAYLOAD_OPACITY = "0;0.96;0.96;0";

export function PipeNetwork() {
  return (
    <div className="pipe-network" aria-hidden="true">
      {/* Viewport-locked accent border — thin purple tubing */}
      <svg
        className="pipe-border"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        {BORDER_RUNS.map((d) => (
          <path key={d} className="pipe-border__run" d={d} />
        ))}
      </svg>

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
