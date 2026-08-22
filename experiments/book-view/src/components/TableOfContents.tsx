import type { BookSkeleton, SkeletonFamily } from "../types";
import { useBookOptions } from "../hooks/useBookOptions";

const CLASS_ACCENT: Record<string, string> = {
  Mammalia: "var(--mammalia)",
  Aves: "var(--aves)",
  Chondrichthyes: "var(--chondrichthyes)",
  Reptilia: "var(--reptilia)",
  // Plantae classes all share one accent (--plantae) rather than inventing a
  // distinct hue per class the way Animalia's core four have - only Aves
  // etc. also get a dedicated color; the rest of Animalia's Parts already
  // fall back to var(--ink) via the `?? "var(--ink)"` below, same pattern.
  Pinopsida: "var(--plantae)",
  Cycadopsida: "var(--plantae)",
  Ginkgoopsida: "var(--plantae)",
  Gnetopsida: "var(--plantae)",
  Lycopodiopsida: "var(--plantae)",
  Polypodiopsida: "var(--plantae)",
  Takakiopsida: "var(--plantae)",
};

// A family with zero enriched species reads as "empty" here the same way
// FamilySection.tsx treats it - missing chapterStats means we can't confirm
// emptiness, so it stays visible rather than risk hiding real content.
function isEmpty(family: SkeletonFamily): boolean {
  return family.chapterStats !== undefined && family.chapterStats.enrichedCount === 0;
}

export function TableOfContents({
  skeleton,
  onSelectChapter,
}: {
  skeleton: BookSkeleton;
  onSelectChapter: (orderFile: string) => void;
}) {
  const { showEmptyFamilies } = useBookOptions();

  // Pure derivation (no mutable variable reassigned across iterations,
  // per the react-hooks/immutability lint rule) - each visible part is
  // paired with whether it's the first part of a new kingdom, compared
  // against the previous *visible* part (array index, not skeleton index)
  // so a fully-filtered-out part never leaves a duplicate or missing
  // "Kingdom" header.
  const visibleParts = skeleton.parts
    .map((part) => ({
      part,
      chapters: part.chapters
        .map((chapter) => ({
          ...chapter,
          families: showEmptyFamilies ? chapter.families : chapter.families.filter((f) => !isEmpty(f)),
        }))
        .filter((chapter) => chapter.families.length > 0),
    }))
    .filter((entry) => entry.chapters.length > 0)
    .map((entry, i, arr) => ({
      ...entry,
      showKingdomHeader: i === 0 || arr[i - 1].part.kingdom !== entry.part.kingdom,
      isFirstKingdom: i === 0,
    }));

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "5rem 1.5rem 6rem" }}>
      {visibleParts.map(({ part, chapters, showKingdomHeader, isFirstKingdom }) => {
        return (
          <div key={part.title}>
            {showKingdomHeader && (
              <div
                style={{
                  textAlign: "center",
                  margin: isFirstKingdom ? "0 0 4rem" : "6rem 0 4rem",
                }}
              >
                <p
                  style={{
                    fontFamily: "var(--font-display)",
                    fontStyle: "italic",
                    color: "var(--ink-faint)",
                    letterSpacing: "0.05em",
                  }}
                >
                  Kingdom
                </p>
                <h1 style={{ fontSize: "2.6rem", letterSpacing: "0.06em" }}>{part.kingdom}</h1>
              </div>
            )}
            <section style={{ marginBottom: "3.5rem" }}>
            <h2
              style={{
                fontSize: "1.6rem",
                color: CLASS_ACCENT[part.className] ?? "var(--ink)",
                borderBottom: `2px solid ${CLASS_ACCENT[part.className] ?? "var(--rule-gold)"}`,
                paddingBottom: "0.5rem",
                marginBottom: "1.25rem",
              }}
            >
              {part.title}
            </h2>
            {chapters.map((chapter) => (
              <button
                key={chapter.orderFile}
                onClick={() => onSelectChapter(chapter.orderFile)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  background: "none",
                  border: "none",
                  borderBottom: "1px solid var(--paper-shadow)",
                  padding: "0.9rem 0.25rem",
                  cursor: "pointer",
                  color: "var(--ink)",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "1.15rem",
                    fontWeight: 600,
                  }}
                >
                  {chapter.title}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--ink-faint)", marginTop: "0.15rem" }}>
                  {chapter.families
                    .map((f) => `${f.commonName ?? f.name} (${f.speciesCount})`)
                    .join(" · ")}
                </div>
              </button>
            ))}
            </section>
          </div>
        );
      })}
    </div>
  );
}
