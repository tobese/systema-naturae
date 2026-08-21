import { useEffect, useState } from "react";
import { CoverSplash } from "./components/CoverSplash";
import { TableOfContents } from "./components/TableOfContents";
import { ChapterPage } from "./components/ChapterPage";
import { Breadcrumb } from "./components/Breadcrumb";
import { useBookData } from "./hooks/useBookData";
import { PART_INTROS } from "./curatedParts";

type Phase = "cover" | "toc" | "chapter";

export default function App() {
  const [phase, setPhase] = useState<Phase>("cover");
  const [activeOrderFile, setActiveOrderFile] = useState<string | null>(null);
  const { skeleton, loading, loadChapter, isChapterLoading, getChapter } = useBookData();

  const handleSelectChapter = (orderFile: string) => {
    setActiveOrderFile(orderFile);
    setPhase("chapter");
    loadChapter(orderFile);
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
  const isFirstChapterOfPart = activePart ? activePart.chapters[0].orderFile === activeOrderFile : false;
  const activeChapterDoc = activeOrderFile ? getChapter(activeOrderFile) : undefined;

  return (
    <div>
      <Breadcrumb
        partTitle={phase === "chapter" ? activePart?.title : undefined}
        chapterTitle={phase === "chapter" ? activeChapterMeta?.title : undefined}
        onHome={() => setPhase("toc")}
      />

      {phase === "toc" && <TableOfContents skeleton={skeleton} onSelectChapter={handleSelectChapter} />}

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
