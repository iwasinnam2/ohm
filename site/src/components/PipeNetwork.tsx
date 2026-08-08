/** Dark graphite tubes + thin purple border rails + sparse purple payloads.
 *
 * Mesh stays nearly silent; only payloads read bright. Accent rails live in
 * the page margin outside the text column: foot at the viewport edge, rise in
 * the outer gutter, ceiling curves toward withOhm (mirrored on the right).
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
 * Thin purple neon rails — open frame in the page margin (outside the text).
 *
 * SVG is full-bleed with a tiny inset; paths hug the outer edges so rails
 * clear the content column entirely. Foot flares to the viewport; rise stays
 * in the margin band; ceiling curves in toward withOhm and ceases.
 */
const BORDER_RUNS = [
  // Left — outer margin: foot at viewport, rise near left edge, ceiling into brand
  "M 0.15 99.6 C 0.05 95 0.4 91 1.2 88 V 11 C 1.2 5.5 6 2.6 18 2.1",
  // Right — mirror
  "M 99.85 99.6 C 99.95 95 99.6 91 98.8 88 V 11 C 98.8 5.5 94 2.6 82 2.1",
] as const;

/** Sharp fade windows — mostly solid mid-run, brief ease at ends. */
const PAYLOAD_OPACITY_TIMES = "0;0.035;0.965;1";
const PAYLOAD_OPACITY = "0;1;1;0";
const PAYLOAD_SPLINES = "0.25 0.1 0.25 1;0 0 1 1;0.25 0.1 0.25 1";

export function PipeNetwork() {
  return (
    <div className="pipe-network" aria-hidden="true">
      {/* Margin-band accent rails — outside the text column */}
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
