import type { BookSkeleton, SkeletonFamily } from "../types";
import { useBookOptions } from "../hooks/useBookOptions";

const CLASS_ACCENT: Record<string, string> = {
  Mammalia: "var(--mammalia)",
  Aves: "var(--aves)",
  Chondrichthyes: "var(--chondrichthyes)",
  Reptilia: "var(--reptilia)",
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

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "5rem 1.5rem 6rem" }}>
      <div style={{ textAlign: "center", marginBottom: "4rem" }}>
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
        <h1 style={{ fontSize: "2.6rem", letterSpacing: "0.06em" }}>{skeleton.kingdom}</h1>
      </div>

      {skeleton.parts.map((part) => {
        const chapters = part.chapters
          .map((chapter) => ({
            ...chapter,
            families: showEmptyFamilies ? chapter.families : chapter.families.filter((f) => !isEmpty(f)),
          }))
          .filter((chapter) => chapter.families.length > 0);

        if (chapters.length === 0) return null;

        return (
          <section key={part.title} style={{ marginBottom: "3.5rem" }}>
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
        );
      })}
    </div>
  );
}
