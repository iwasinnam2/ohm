/** Dark graphite tubes + thin purple border rails + sparse purple payloads.
 *
 * Mesh stays nearly silent; only payloads read bright. Accent rails frame
 * the content column: adjacent to the docs/index edge, curve to the ceiling
 * at withOhm (mirrored on the right), feet flare outward and cease.
 */

type Track = {
  d: string;
  /** Motion duration when a payload rides this run. */
  dur?: string;
  delay?: string;
  soft?: boolean;
  /** When false, tube only — no animated payload (cheaper). */
  payload?: boolean;
};

/** Spacious orthographic mesh — viewBox 1200×800. */
const TRACKS: readonly Track[] = [
  {
    d: "M -80 110 H 640 Q 700 110 700 170 V 260 Q 700 320 760 320 H 1280",
    dur: "14s",
    delay: "0s",
  },
  {
    d: "M 1280 400 H 560 Q 500 400 500 460 V 540 Q 500 600 440 600 H -80",
    dur: "15s",
    delay: "2.2s",
  },
  {
    d: "M -80 720 H 520 Q 580 720 580 660 V 580 Q 580 520 640 520 H 1280",
    dur: "16s",
    delay: "4.5s",
  },
  {
    d: "M 180 -60 V 240 Q 180 300 240 300 H 380 Q 440 300 440 360 V 860",
    dur: "13.5s",
    delay: "1.1s",
  },
  {
    d: "M 1020 860 V 480 Q 1020 420 960 420 H 820 Q 760 420 760 360 V -60",
    dur: "14.5s",
    delay: "3.4s",
  },
  {
    d: "M 600 -60 V 200 Q 600 260 520 260 H 300 Q 240 260 240 320 V 860",
    payload: false,
  },
  {
    d: "M 48 860 V 420 Q 48 360 110 360 H 260 Q 320 360 320 300 V -60",
    soft: true,
    payload: false,
  },
  {
    d: "M 1152 -60 V 280 Q 1152 340 1090 340 H 920 Q 860 340 860 400 V 860",
    soft: true,
    payload: false,
  },
] as const;

/**
 * Thin purple neon rails — open frame beside the content column.
 *
 * Left: flares out at the foot → rises just left of the docs/index column →
 * curves up to the ceiling at withOhm and ceases.
 * Right: mirror (ceiling cease at the opposite header end).
 * No continuous top or bottom bar.
 */
const BORDER_RUNS = [
  // Left — foot flares out to the page edge, rises beside docs/index, ceiling into withOhm
  "M 0.5 99.4 C 0.2 95.2 2.2 91.5 8.2 88.8 V 12.2 C 8.2 6.4 11.2 3.2 22 2.4",
  // Right — mirror
  "M 99.5 99.4 C 99.8 95.2 97.8 91.5 91.8 88.8 V 12.2 C 91.8 6.4 88.8 3.2 78 2.4",
] as const;

/** Sharp fade windows — mostly solid mid-run, brief ease at ends. */
const PAYLOAD_OPACITY_TIMES = "0;0.035;0.965;1";
const PAYLOAD_OPACITY = "0;1;1;0";
const PAYLOAD_SPLINES = "0.25 0.1 0.25 1;0 0 1 1;0.25 0.1 0.25 1";

export function PipeNetwork() {
  return (
    <div className="pipe-network" aria-hidden="true">
      {/* Content-locked accent rails — thin purple neon tubing */}
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

        {TRACKS.map((track, i) => {
          if (track.payload === false || !track.dur) return null;
          return (
            <ellipse
              key={`payload-${i}`}
              className="pipe-network__payload"
              rx={2.75}
              ry={0.95}
              cx={0}
              cy={0}
            >
              <animateMotion
                dur={track.dur}
                begin={track.delay ?? "0s"}
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
                keySplines={PAYLOAD_SPLINES}
                dur={track.dur}
                begin={track.delay ?? "0s"}
                repeatCount="indefinite"
              />
            </ellipse>
          );
        })}
      </svg>
    </div>
  );
}
