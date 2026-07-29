type OhmMarkProps = {
  className?: string;
  title?: string;
};

/**
 * Brand mark: Greek capital omega (Ω) — the Ohm symbol.
 * Uses the Unicode glyph so it reads as Ω, not a paren/horseshoe sketch.
 */
export function OhmMark({ className, title = "Ohm" }: OhmMarkProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={title}
    >
      <title>{title}</title>
      <text
        className="ohm-mark-path ohm-mark-glyph"
        x="32"
        y="33"
        textAnchor="middle"
        dominantBaseline="central"
        fill="currentColor"
        fontFamily="Georgia, 'Times New Roman', 'Noto Serif', 'Liberation Serif', serif"
        fontSize="50"
        fontWeight="700"
      >
        {"\u03A9"}
      </text>
    </svg>
  );
}
