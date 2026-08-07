/** Visual value system for Brand docs — core design principles. */

const VALUES = [
  {
    id: "crossing",
    title: "Crossing truth",
    body: "Every request is HIT or MISS and always metered. Ohm rents the pipe — not lab wholesale.",
  },
  {
    id: "exact",
    title: "Exact replay",
    body: "Identical requests only. No semantic or fuzzy cache theatre.",
  },
  {
    id: "custody",
    title: "Bearer custody",
    body: "Email/password restores your Intermediate key. Possession is full tenant authority.",
  },
  {
    id: "labs",
    title: "Labs stay labs",
    body: "BYOK generation stays with providers. Ohm is the traffic utility, not a model lab.",
  },
  {
    id: "browse",
    title: "Governed browse",
    body: "Public web only through purpose, robots, SSRF, and PII gates.",
  },
  {
    id: "verify",
    title: "Verifiable claims",
    body: "Meters and waste demos bind marketing to machinery.",
  },
] as const;

export function BrandValuesAid() {
  return (
    <section className="brand-values" aria-labelledby="brand-values-label">
      <h2 id="brand-values-label" className="brand-values__title">
        Value system
      </h2>
      <p className="brand-values__lede">
        Design principles for the AI traffic utility — what we optimize for and
        what we refuse.
      </p>
      <ul className="brand-values__grid">
        {VALUES.map((v) => (
          <li key={v.id} className="brand-values__card">
            <strong className="brand-values__name">{v.title}</strong>
            <span className="brand-values__body">{v.body}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
