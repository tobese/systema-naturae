import type { ChapterDoc } from "../types";
import { FamilySection } from "./FamilySection";
import { useReadingWindow } from "../hooks/useReadingWindow";

export function ChapterPage({
  chapter,
  partTitle,
  partIntro,
  showPartIntro,
}: {
  chapter: ChapterDoc;
  partTitle: string;
  partIntro: string;
  showPartIntro: boolean;
}) {
  const familySlugs = chapter.families.map((f) => f.familySlug).filter((s): s is string => Boolean(s));
  const readingWindow = useReadingWindow(familySlugs);

  return (
    <article style={{ maxWidth: 680, margin: "0 auto", padding: "3rem 1.5rem 8rem" }}>
      {showPartIntro && (
        <header style={{ marginBottom: "4rem", textAlign: "center" }}>
          <h1 style={{ fontSize: "2rem", letterSpacing: "0.04em" }}>{partTitle}</h1>
          <p
            style={{
              marginTop: "1.25rem",
              fontSize: "1.05rem",
              lineHeight: 1.75,
              color: "var(--ink-soft)",
              textAlign: "left",
            }}
          >
            {partIntro}
          </p>
        </header>
      )}

      <header>
        <h2 style={{ fontSize: "1.7rem" }}>{chapter.title}</h2>
        {chapter.description && (
          <p style={{ marginTop: "0.9rem", fontSize: "1rem", lineHeight: 1.75, color: "var(--ink-soft)" }}>
            {chapter.description}
          </p>
        )}
      </header>

      {chapter.families.map((family) => (
        <FamilySection key={family.id} family={family} readingWindow={readingWindow} />
      ))}
    </article>
  );
}
