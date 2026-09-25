import type { BookSkeleton, Kingdom } from "@shared/book/types";
import { useBookOptions } from "@shared/book/hooks/useBookOptions";
import { ForeEdgeIndex } from "./ForeEdgeIndex";
import { KINGDOM_INTROS } from "../kingdomIntros";
import { isEmptyFamily } from "@shared/book/lib/chapterVisibility";

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

// Fungi has 51 classes (all "-mycetes") - rather than hardcode each one into
// CLASS_ACCENT like Plantae's handful, resolve by kingdom as a fallback
// below CLASS_ACCENT so any future per-class override still wins. Also
// doubles as the fore-edge index's per-kingdom tab color - Animalia has no
// single dedicated hue (it splits by class via CLASS_ACCENT) so its tab
// reads as plain ink, same as any animal class without its own accent.
const KINGDOM_ACCENT: Record<string, string> = {
  Animalia: "var(--ink)",
  Plantae: "var(--plantae)",
  Fungi: "var(--fungi)",
  Chromista: "var(--chromista)",
  Protozoa: "var(--protozoa)",
  Archaea: "var(--archaea)",
};

export function TableOfContents({
  skeleton,
  onSelectChapter,
}: {
  skeleton: BookSkeleton;
  onSelectChapter: (orderFile: string) => void;
  onSelectKingdom: (kingdom: Kingdom) => void;
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
          families: showEmptyFamilies ? chapter.families : chapter.families.filter((f) => !isEmptyFamily(f)),
        }))
        .filter((chapter) => chapter.families.length > 0),
    }))
    .filter((entry) => entry.chapters.length > 0)
    .map((entry, i, arr) => ({
      ...entry,
      showKingdomHeader: i === 0 || arr[i - 1].part.kingdom !== entry.part.kingdom,
      isFirstKingdom: i === 0,
    }));

  // One fore-edge tab per kingdom, each carrying the ordered, deduped list
  // of classes (Parts) it contains - the "next level" tags shown on click.
  const edgeEntries = (() => {
    const byKingdom = new Map<Kingdom, { className: string; title: string }[]>();
    for (const { part } of visibleParts) {
      const classes = byKingdom.get(part.kingdom) ?? [];
      if (!classes.some((c) => c.className === part.className)) {
        classes.push({ className: part.className, title: part.title });
      }
      byKingdom.set(part.kingdom, classes);
    }
    return [...byKingdom.entries()].map(([kingdom, classes]) => ({
      kingdom,
      color: KINGDOM_ACCENT[kingdom] ?? "var(--ink)",
      classes,
    }));
  })();

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "5rem 1.5rem 6rem" }}>
      <ForeEdgeIndex entries={edgeEntries} />
      {visibleParts.map(({ part, chapters, showKingdomHeader, isFirstKingdom }) => {
        return (
          <div key={part.title} id={showKingdomHeader ? `kingdom-${part.kingdom}` : undefined}>
            {showKingdomHeader && (
              <header style={{ margin: isFirstKingdom ? "0 0 3rem" : "6rem 0 3rem" }}>
                <div style={{ textAlign: "center" }}>
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
                  <div style={{ width: "70px", height: "1px", background: "var(--rule-gold)", margin: "1.5rem auto 2.5rem" }} />
                </div>
                {KINGDOM_INTROS[part.kingdom].map((paragraph, i) => (
                  <p key={i} style={{ fontSize: "1.05rem", lineHeight: 1.8, color: "var(--ink-soft)", marginBottom: "1.25rem" }}>
                    {i === 0 ? (
                      <>
                        <span
                          aria-hidden
                          style={{
                            fontFamily: "var(--font-display)",
                            fontSize: "3.4rem",
                            lineHeight: "2.5rem",
                            float: "left",
                            marginRight: "0.5rem",
                            marginTop: "0.35rem",
                            color: "var(--rule-gold)",
                          }}
                        >
                          {paragraph.charAt(0)}
                        </span>
                        {paragraph.slice(1)}
                      </>
                    ) : (
                      paragraph
                    )}
                  </p>
                ))}
              </header>
            )}
            <section id={`class-${part.kingdom}-${part.className}`} style={{ marginBottom: "3.5rem" }}>
            <h2
              style={{
                fontSize: "1.6rem",
                color: CLASS_ACCENT[part.className] ?? KINGDOM_ACCENT[part.kingdom] ?? "var(--ink)",
                borderBottom: `2px solid ${CLASS_ACCENT[part.className] ?? KINGDOM_ACCENT[part.kingdom] ?? "var(--rule-gold)"}`,
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
