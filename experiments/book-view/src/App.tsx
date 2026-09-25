import { useEffect, useState } from "react";
import { CoverSplash } from "./components/CoverSplash";
import { TableOfContents } from "./components/TableOfContents";
import { ChapterPage } from "@shared/book/components/ChapterPage";
import { KingdomIntroPage } from "./components/KingdomIntroPage";
import { Breadcrumb } from "./components/Breadcrumb";
import { useBookData } from "./hooks/useBookData";
import { useBookOptions } from "@shared/book/hooks/useBookOptions";
import { PART_INTROS } from "./curatedParts";
import { firstVisibleChapter } from "@shared/book/lib/chapterVisibility";
import type { Kingdom } from "@shared/book/types";

type Phase = "cover" | "toc" | "kingdomIntro" | "chapter";

export default function App() {
  const [phase, setPhase] = useState<Phase>("cover");
  const [activeOrderFile, setActiveOrderFile] = useState<string | null>(null);
  const [activeKingdom, setActiveKingdom] = useState<Kingdom | null>(null);
  const { skeleton, loading, loadChapter, isChapterLoading, getChapter } = useBookData();
  const { showEmptyFamilies } = useBookOptions();

  const handleSelectChapter = (orderFile: string) => {
    setActiveOrderFile(orderFile);
    setPhase("chapter");
    loadChapter(orderFile);
  };

  const handleSelectKingdom = (kingdom: Kingdom) => {
    setActiveKingdom(kingdom);
    setPhase("kingdomIntro");
  };

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [phase, activeOrderFile]);

  if (phase === "cover") {
    return <CoverSplash onOpen={() => setPhase("toc")} />;
  }

  if (loading || !skeleton) {
    return (
      <div style={{ padding: "4rem", textAlign: "center", color: "var(--ink-faint)" }}>
        Opening the book…
      </div>
    );
  }

  const activePart = activeOrderFile
    ? skeleton.parts.find((p) => p.chapters.some((c) => c.orderFile === activeOrderFile))
    : undefined;
  const activeChapterMeta = activePart?.chapters.find((c) => c.orderFile === activeOrderFile);
  const isFirstChapterOfPart = activePart
    ? firstVisibleChapter(activePart, showEmptyFamilies)?.orderFile === activeOrderFile
    : false;
  const activeChapterDoc = activeOrderFile ? getChapter(activeOrderFile) : undefined;

  return (
    <div>
      <Breadcrumb
        partTitle={
          phase === "chapter" ? activePart?.title : phase === "kingdomIntro" ? activeKingdom ?? undefined : undefined
        }
        chapterTitle={phase === "chapter" ? activeChapterMeta?.title : undefined}
        onHome={() => setPhase("toc")}
      />

      {phase === "toc" && (
        <TableOfContents skeleton={skeleton} onSelectChapter={handleSelectChapter} onSelectKingdom={handleSelectKingdom} />
      )}

      {phase === "kingdomIntro" && activeKingdom && <KingdomIntroPage kingdom={activeKingdom} />}

      {phase === "chapter" && activeOrderFile && (
        <>
          {isChapterLoading(activeOrderFile) || !activeChapterDoc ? (
            <div style={{ padding: "4rem", textAlign: "center", color: "var(--ink-faint)" }}>
              Turning to {activeChapterMeta?.title}…
            </div>
          ) : (
            <ChapterPage
              chapter={activeChapterDoc}
              partTitle={activePart!.title}
              partIntro={PART_INTROS[activePart!.className] ?? activePart!.description ?? ""}
              partCollage={activePart!.collage ?? []}
              showPartIntro={isFirstChapterOfPart}
            />
          )}
        </>
      )}
    </div>
  );
}
