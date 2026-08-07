/** Enablement feature grid — inventory ops instead of wasteful re-pays. */

type Feature = {
  title: string;
  body: string;
  icon: "replay" | "tree" | "promote" | "compose" | "browse" | "audit";
};

const FEATURES: Feature[] = [
  {
    icon: "replay",
    title: "Zero-upstream replay",
    body: "Identical requests answer from Redis. The lab is not paid twice.",
  },
  {
    icon: "tree",
    title: "Tree-scoped isolation",
    body: "PR and agent inventories diverge without cloning tenants or databases.",
  },
  {
    icon: "promote",
    title: "Promote as index work",
    body: "Bring new digests to main without rewriting history as a bulk export.",
  },
  {
    icon: "compose",
    title: "Compose with a DB preview",
    body: "State branch + replay tip in one CI job — complementary peers.",
  },
  {
    icon: "browse",
    title: "Governed browse",
    body: "Public web through robots / PII / SSRF before model contact.",
  },
  {
    icon: "audit",
    title: "Auditable claims",
    body: "Meters and the waste demo bind marketing to machinery.",
  },
];

function FeatureIcon({ name }: { name: Feature["icon"] }) {
  const common = {
    width: 22,
    height: 22,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "replay":
      return (
        <svg {...common}>
          <path d="M3 12a9 9 0 1 0 3-6.7" />
          <path d="M3 4v5h5" />
          <path d="M12 7v5l3 2" />
        </svg>
      );
    case "tree":
      return (
        <svg
          className="enablement__payload-tree"
          width={20}
          height={20}
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          {/* thin trunk → fork → tips; payload nodes as light diamonds */}
          <path
            className="enablement__payload-tree-edge"
            d="M12 4.5v6.5M12 11l-5.5 4.5M12 11l5.5 4.5"
            stroke="currentColor"
            strokeWidth="1.15"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <rect
            className="enablement__payload-tree-node"
            x="10.35"
            y="2.6"
            width="3.3"
            height="3.3"
            rx="0.55"
            transform="rotate(45 12 4.25)"
            fill="currentColor"
            stroke="none"
          />
          <rect
            className="enablement__payload-tree-node"
            x="4.85"
            y="13.85"
            width="3.1"
            height="3.1"
            rx="0.5"
            transform="rotate(45 6.4 15.4)"
            fill="currentColor"
            stroke="none"
          />
          <rect
            className="enablement__payload-tree-node"
            x="15.95"
            y="13.85"
            width="3.1"
            height="3.1"
            rx="0.5"
            transform="rotate(45 17.5 15.4)"
            fill="currentColor"
            stroke="none"
          />
        </svg>
      );
    case "promote":
      return (
        <svg {...common}>
          <path d="M12 19V5" />
          <path d="M7 10l5-5 5 5" />
          <path d="M5 19h14" />
        </svg>
      );
    case "compose":
      return (
        <svg {...common}>
          <rect x="3" y="4" width="18" height="7" rx="1.5" />
          <rect x="3" y="13" width="18" height="7" rx="1.5" />
          <path d="M8 7.5h8M8 16.5h5" />
        </svg>
      );
    case "browse":
      return (
        <svg {...common}>
          <path d="M12 3l7 3v5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V6z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      );
    case "audit":
      return (
        <svg {...common}>
          <path d="M8 3h6l4 4v14H8z" />
          <path d="M14 3v4h4" />
          <path d="M10 12h6M10 16h4" />
          <path d="M10 9.5l1.2 1.2 2.3-2.4" />
        </svg>
      );
    default:
      return null;
  }
}

type Props = {
  /** Show section heading (product landing). Hide when parent md already has h2. */
  showHeading?: boolean;
};

export function EnablementFeatures({ showHeading = true }: Props) {
  return (
    <section
      className="enablement"
      aria-labelledby={showHeading ? "enablement-label" : undefined}
      aria-label={showHeading ? undefined : "What this architecture enables"}
    >
      {showHeading ? (
        <h2 id="enablement-label" className="enablement__title">
          What this architecture enables
        </h2>
      ) : null}
      <p className="enablement__lede">
        This design turns traditionally wasteful AI operations — re-paying
        identical agent and CI prompts, mixing preview pollution into production
        HIT inventory — into{" "}
        <strong>inventory and metadata operations</strong>.
      </p>
      <ul className="enablement__grid">
        {FEATURES.map((f, i) => (
          <li
            key={f.title}
            className="enablement__card"
            style={{ animationDelay: `${80 + i * 55}ms` }}
          >
            <span
              className={
                f.icon === "tree"
                  ? "enablement__icon enablement__icon--payload-tree"
                  : "enablement__icon"
              }
              aria-hidden="true"
            >
              <FeatureIcon name={f.icon} />
            </span>
            <h3 className="enablement__card-title">{f.title}</h3>
            <p className="enablement__card-body">{f.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
