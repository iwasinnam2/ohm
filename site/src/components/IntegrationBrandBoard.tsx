import Link from "next/link";
import {
  BRAND_KIND_LABEL,
  INTEGRATION_BRANDS,
  type BrandTile,
} from "@/lib/integrationBrands";

function BrandCard({ brand }: { brand: BrandTile }) {
  const external = brand.authorizeHref.startsWith("http");
  return (
    <li className="brand-tile">
      <div className="brand-tile__outer">
        <span
          className="brand-tile__logo"
          style={{ background: brand.markColor }}
          aria-hidden="true"
        >
          {brand.mark}
        </span>
        <div className="brand-tile__copy">
          <span className="brand-tile__name">{brand.name}</span>
          <span className="brand-tile__blurb">{brand.blurb}</span>
        </div>
      </div>
      <div className="brand-tile__actions">
        <a
          className="btn btn--primary brand-tile__integrate"
          href={brand.authorizeHref}
          target={external ? "_blank" : undefined}
          rel={external ? "noopener noreferrer" : undefined}
        >
          Integrate
        </a>
        <a
          className="brand-tile__setup"
          href={brand.href}
          target={brand.href.startsWith("http") ? "_blank" : undefined}
          rel={
            brand.href.startsWith("http") ? "noopener noreferrer" : undefined
          }
        >
          Visit site
        </a>
      </div>
      <p className="brand-tile__perm">
        Opens {brand.name} and prompts authorization for withOhm read/write
        access on that platform where supported.
      </p>
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
          One-click integrate — authorize withOhm on the tools you already use.
          Each Integrate button opens the platform and requests read/write
          permissions where the vendor supports OAuth or marketplace attach.
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
      <p className="brand-board__foot">
        Prefer the connections workbench?{" "}
        <Link href="/connections">Open Connections</Link>.
      </p>
    </div>
  );
}
