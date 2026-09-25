import { useEffect, useMemo } from "react";
import "@shared/book/book.css";
import { BookOptionsProvider } from "@shared/book/context/BookOptions";
import { ChapterPage } from "@shared/book/components/ChapterPage";
import { firstVisibleChapter } from "@shared/book/lib/chapterVisibility";
import { useBookChapters } from "../hooks/useBookChapters";

// The portal's Book viewMode: the standalone book's reading surface, mounted
// as a paper page inside the portal shell. The host supplies only *where to
// start* - which order (chapter) and which family - and the book renders
// itself; see docs/book-integration-plan.md.
//
// Navigation deliberately stays host-driven for now: the portal's header and
// left taxonomy sidebar already know where the reader is, and the book's own
// chrome (cover, table of contents, fore-edge index) belongs to the standalone
// app for the time being.

interface Props {
  kingdom: string;
  /** Lowercase order id stem of the chapter to show ("carnivora"). */
  orderName: string | null;
  /** Family to open the chapter at, when the host knows one. */
  focusFamilySlug?: string;
}

export function BookReadingPane({ kingdom, orderName, focusFamilySlug }: Props) {
  const { skeleton, failed, loadChapter, getChapter } = useBookChapters(kingdom);

  const parts = useMemo(
    () => (skeleton?.parts ?? []).filter((p) => p.kingdom.toLowerCase() === kingdom),
    [skeleton, kingdom],
  );

  // Nothing selected yet: fall back to the first visible chapter of the first
  // part, so the pane is never blank.
  const fallbackOrderName = useMemo(() => {
    const part = parts[0];
    if (!part) return null;
    return (firstVisibleChapter(part, false) ?? part.chapters[0])?.orderName ?? null;
  }, [parts]);

  const target = orderName ?? fallbackOrderName;

  useEffect(() => {
    if (target) loadChapter(target);
  }, [target, loadChapter]);

  const entry = target ? getChapter(target) : undefined;

  // The part intro (title, prose, collage) belongs to the part's first
  // visible chapter only - the same rule the standalone uses.
  const showPartIntro = useMemo(() => {
    if (!entry) return false;
    const part = parts.find((p) => p.chapters.some((c) => c.orderFile === entry.meta.orderFile));
    if (!part) return false;
    return (firstVisibleChapter(part, false) ?? part.chapters[0])?.orderFile === entry.meta.orderFile;
  }, [entry, parts]);

  return (
    <div className="book-surface" style={{ height: "100%", overflowY: "auto" }}>
      {failed ? (
        <div style={{ padding: "3rem", textAlign: "center", color: "var(--ink-faint)" }}>
          <p>No book data generated yet.</p>
          <p style={{ fontSize: "0.85rem" }}>
            Run <code>npm run build:book</code> in <code>portal/</code> to build the sidecars.
          </p>
        </div>
      ) : !entry ? (
        <div style={{ padding: "3rem", textAlign: "center", color: "var(--ink-faint)" }}>
          {target ? `Opening ${target}…` : "No chapters available for this kingdom."}
        </div>
      ) : (
        <BookOptionsProvider>
          <ChapterPage
            chapter={entry.chapter}
            partTitle={entry.partTitle}
            partIntro={entry.partIntro}
            partCollage={entry.partCollage}
            showPartIntro={showPartIntro}
            focusFamilySlug={focusFamilySlug}
          />
        </BookOptionsProvider>
      )}
    </div>
  );
}
