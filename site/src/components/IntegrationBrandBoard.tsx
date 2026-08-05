import Link from "next/link";
import {
  BRAND_KIND_LABEL,
  INTEGRATION_BRANDS,
  type BrandTile,
} from "@/lib/integrationBrands";

function BrandCard({ brand }: { brand: BrandTile }) {
  return (
    <li className="brand-tile">
      <a
        className="brand-tile__outer"
        href={brand.href}
        target={brand.href.startsWith("http") ? "_blank" : undefined}
        rel={brand.href.startsWith("http") ? "noopener noreferrer" : undefined}
      >
        <span className="brand-tile__name">{brand.name}</span>
        <span className="brand-tile__blurb">{brand.blurb}</span>
      </a>
      {brand.setupHref ? (
        <Link className="brand-tile__setup" href={brand.setupHref}>
          Set up →
        </Link>
      ) : null}
    </li>
  );
}

export function IntegrationBrandBoard({
  showIntro = true,
}: {
  showIntro?: boolean;
}) {
  const kinds: BrandTile["kind"][] = ["agent", "pipe", "surface"];
  return (
    <div className="brand-board">
      {showIntro ? (
        <p className="brand-board__lede">
          Interconnectedness and accessibility — withOhm sits in the middle of
          tools you already use. Tap a brand for their home; <em>Set up</em>{" "}
          wires withOhm.
        </p>
      ) : null}
      {kinds.map((kind) => {
        const tiles = INTEGRATION_BRANDS.filter((b) => b.kind === kind);
        return (
          <section
            key={kind}
            className="brand-board__group"
            aria-labelledby={`brand-kind-${kind}`}
          >
            <h2 className="brand-board__group-title" id={`brand-kind-${kind}`}>
              {BRAND_KIND_LABEL[kind]}
            </h2>
            <ul className="brand-board__grid">
              {tiles.map((brand) => (
                <BrandCard key={brand.id} brand={brand} />
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
