import { useEffect } from "react";
import type { ChapterDoc, CollageEntry } from "../types";
import { FamilySection } from "./FamilySection";
import { PartCollage } from "./PartCollage";
import { useReadingWindow } from "../hooks/useReadingWindow";
import { paragraphs } from "../lib/paragraphs";

export function ChapterPage({
  chapter,
  partTitle,
  partIntro,
  partCollage,
  showPartIntro,
  focusFamilySlug,
}: {
  chapter: ChapterDoc;
  partTitle: string;
  partIntro: string;
  partCollage: CollageEntry[];
  showPartIntro: boolean;
  // Host-driven scroll target: the portal passes the family the reader
  // navigated from so the chapter opens there instead of at its first
  // family. Omitted by the standalone.
  focusFamilySlug?: string;
}) {
  const familySlugs = chapter.families.map((f) => f.familySlug).filter((s): s is string => Boolean(s));
  const readingWindow = useReadingWindow(familySlugs, focusFamilySlug);

  // Scroll after mount: the family <details> shells render immediately (only
  // their contents are window-gated), so the target exists on the first frame.
  useEffect(() => {
    if (!focusFamilySlug) return;
    const el = document.getElementById(`family-${focusFamilySlug}`);
    if (el) el.scrollIntoView({ block: "start" });
  }, [focusFamilySlug]);

  return (
    <article style={{ maxWidth: 680, margin: "0 auto", padding: "3rem 1.5rem 8rem" }}>
      {showPartIntro && (
        <header style={{ marginBottom: "4rem", textAlign: "center" }}>
          <h1 style={{ fontSize: "2rem", letterSpacing: "0.04em" }}>{partTitle}</h1>
          <PartCollage items={partCollage} />
          {paragraphs(partIntro).map((paragraph, i) => (
            <p
              key={i}
              style={{
                marginTop: i === 0 ? "1.25rem" : "1rem",
                fontSize: "1.05rem",
                lineHeight: 1.75,
                color: "var(--ink-soft)",
                textAlign: "left",
              }}
            >
              {paragraph}
            </p>
          ))}
        </header>
      )}

      <header>
        <h2 style={{ fontSize: "1.7rem" }}>{chapter.title}</h2>
        {paragraphs(chapter.description).map((paragraph, i) => (
          <p key={i} style={{ margin: i === 0 ? "0.9rem 0 0" : "0.8rem 0 0", fontSize: "1rem", lineHeight: 1.75, color: "var(--ink-soft)" }}>
            {paragraph}
          </p>
        ))}
      </header>

      {chapter.families.map((family) => (
        <FamilySection key={family.id} family={family} readingWindow={readingWindow} />
      ))}
    </article>
  );
}
