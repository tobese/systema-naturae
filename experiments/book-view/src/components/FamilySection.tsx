import type { BookNode } from "../types";
import { SpeciesEntry } from "./SpeciesEntry";
import { useBookOptions } from "../hooks/useBookOptions";

function isExtinct(node: BookNode): boolean {
  return Boolean(node.extinct || node.fossil);
}

function GenusSection({
  genus,
  index,
  showExtinct,
}: {
  genus: BookNode;
  index: number;
  showExtinct: boolean;
}) {
  const detailed = (genus.children ?? []).filter((s) => showExtinct || !isExtinct(s));
  const stubs = (genus.speciesList ?? []).filter((s) => showExtinct || !isExtinct(s));
  const totalCount = detailed.length + stubs.length;

  return (
    <div id={`genus-${genus.id}`} style={{ marginTop: "1.5rem" }}>
      <h4
        style={{
          fontSize: "1rem",
          fontStyle: "italic",
          color: "var(--ink-soft)",
          marginBottom: "0.3rem",
        }}
      >
        {index}. {genus.name}
        <span style={{ fontStyle: "normal", fontSize: "0.8rem", color: "var(--ink-faint)", marginLeft: "0.5rem" }}>
          {totalCount} {totalCount === 1 ? "species" : "species"}
        </span>
      </h4>

      {detailed.map((species) => (
        <SpeciesEntry key={species.id} species={species} />
      ))}

      {stubs.length > 0 && (
        <p style={{ fontSize: "0.85rem", color: "var(--ink-faint)", margin: "0.5rem 0 0", lineHeight: 1.7 }}>
          Also in this genus: {stubs.map((s) => s.name).join(", ")}.
        </p>
      )}
    </div>
  );
}

// Usually family.children are genera directly, but some families (e.g.
// Cetacea, modeled with a SUBFAMILY/TRIBE layer between family and genus)
// nest deeper — walk down past any non-genus rank to find the real genera.
function collectGenera(node: BookNode): BookNode[] {
  const children = node.children ?? [];
  if (children.length === 0) return [];
  if (children[0].rank === "GENUS") return children;
  return children.flatMap(collectGenera);
}

export function FamilySection({ family }: { family: BookNode }) {
  const { showExtinct } = useBookOptions();
  const genera = collectGenera(family)
    .filter((g) => showExtinct || !isExtinct(g))
    .filter((g) => {
      const detailed = (g.children ?? []).filter((s) => showExtinct || !isExtinct(s));
      const stubs = (g.speciesList ?? []).filter((s) => showExtinct || !isExtinct(s));
      return detailed.length + stubs.length > 0;
    });
  const stats = family.chapterStats;

  if (genera.length === 0) return null;

  return (
    <section id={`family-${family.familySlug}`} style={{ marginTop: "3rem" }}>
      <h3 style={{ fontSize: "1.4rem", borderBottom: "1px solid var(--rule-gold)", paddingBottom: "0.4rem" }}>
        {family.name}
        {family.commonName && (
          <span style={{ fontFamily: "var(--font-body)", fontWeight: 400, fontSize: "1rem", color: "var(--ink-faint)" }}>
            {" "}
            — {family.commonName}
          </span>
        )}
      </h3>
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", fontSize: "0.85rem", color: "var(--ink-faint)", marginTop: "0.3rem" }}>
        <span>{family.speciesCount ?? 0} species</span>
        {family.distribution && <span>{family.distribution}</span>}
        {stats && (
          <span>
            {stats.enrichedCount} of {stats.speciesCount} entries fully described so far
          </span>
        )}
      </div>

      {genera.map((genus, i) => (
        <GenusSection key={genus.id} genus={genus} index={i + 1} showExtinct={showExtinct} />
      ))}
    </section>
  );
}
