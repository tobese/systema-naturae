import type { BookNode } from "../types";
import type { ReadingWindow } from "../hooks/useReadingWindow";
import { SpeciesEntry } from "./SpeciesEntry";
import { useBookOptions } from "../hooks/useBookOptions";

function isExtinct(node: BookNode): boolean {
  return Boolean(node.extinct || node.fossil);
}

function GenusSection({
  genus,
  index,
  showExtinct,
  showStubs,
}: {
  genus: BookNode;
  index: number;
  showExtinct: boolean;
  showStubs: boolean;
}) {
  const detailed = (genus.children ?? []).filter((s) => showExtinct || !isExtinct(s));
  const rawStubs = (genus.speciesList ?? []).filter((s) => showExtinct || !isExtinct(s));
  const stubs = showStubs ? rawStubs : [];
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

      {genus.description && (
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", margin: "0 0 0.6rem", lineHeight: 1.6 }}>
          {genus.description}
        </p>
      )}

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

export function FamilySection({ family, readingWindow }: { family: BookNode; readingWindow: ReadingWindow }) {
  const { showExtinct, showStubs, showEmptyFamilies } = useBookOptions();
  const stats = family.chapterStats;

  // A family with zero enriched species is "empty" regardless of extinct/
  // stub filtering below - hidden by default so the book doesn't fill up
  // with bare headers once a class's coverage gets patchy (missing
  // chapterStats means we can't confirm emptiness, so don't hide).
  if (!showEmptyFamilies && stats && stats.enrichedCount === 0) return null;

  const genera = collectGenera(family)
    .filter((g) => showExtinct || !isExtinct(g))
    .filter((g) => {
      const detailed = (g.children ?? []).filter((s) => showExtinct || !isExtinct(s));
      const stubs = (showStubs ? g.speciesList ?? [] : []).filter((s) => showExtinct || !isExtinct(s));
      return detailed.length + stubs.length > 0;
    });

  if (genera.length === 0) return null;

  const slug = family.familySlug!;
  const expanded = readingWindow.isExpanded(slug);

  return (
    <details
      id={`family-${slug}`}
      ref={readingWindow.registerSentinel(slug)}
      open={expanded}
      style={{ marginTop: "3rem" }}
    >
      <summary
        style={{ cursor: "pointer", listStyle: "none" }}
        onClick={(e) => {
          // Only a genuine click on a currently-*collapsed* summary counts
          // as a manual pin. The native `toggle` event fires for *any*
          // open-attribute change (including React setting `open` from
          // scroll position), so it can't tell a real click apart from the
          // reading window opening this section on its own - using it here
          // was a real bug: every family that ever became scroll-active got
          // pinned open indefinitely, defeating the whole point of collapse.
          if (!expanded) readingWindow.pin(slug);
          else e.preventDefault(); // let scroll position keep deciding, not a stray close-click
        }}
      >
        <h3
          style={{
            display: "inline",
            fontSize: "1.4rem",
            borderBottom: "1px solid var(--rule-gold)",
            paddingBottom: "0.4rem",
          }}
        >
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
      </summary>

      {expanded && (
        <div>
          {family.description ? (
            <p style={{ margin: "0.8rem 0 0", fontSize: "0.95rem", lineHeight: 1.6, color: "var(--ink-soft)" }}>
              {family.description}
            </p>
          ) : family.notableMembers && family.notableMembers.length > 0 ? (
            <p style={{ margin: "0.8rem 0 0", fontSize: "0.85rem", fontStyle: "italic", color: "var(--ink-faint)" }}>
              Notable: {family.notableMembers.join(", ")}
            </p>
          ) : null}

          {genera.map((genus, i) => (
            <GenusSection key={genus.id} genus={genus} index={i + 1} showExtinct={showExtinct} showStubs={showStubs} />
          ))}
        </div>
      )}
    </details>
  );
}
