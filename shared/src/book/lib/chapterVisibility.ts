import type { SkeletonChapter, SkeletonFamily, SkeletonPart } from "../types";

// A family with zero enriched species reads as "empty" - missing
// chapterStats means we can't confirm emptiness, so it stays visible rather
// than risk hiding real content. Shared between TableOfContents.tsx (which
// chapters/families it lists) and App.tsx (which chapter counts as a Part's
// "first" for showing the Part intro paragraph + collage) so the two can
// never disagree about which chapter a reader actually lands on first -
// they did before this was shared: with "Show empty families" off, 32 of
// 255 Parts have a structurally-first chapter (skeleton order) that's
// entirely empty and so never shown in the Contents list at all, meaning
// the chapter a reader actually clicks as "first" wasn't chapters[0] and
// silently got no collage/intro.
export function isEmptyFamily(family: SkeletonFamily): boolean {
  return family.chapterStats !== undefined && family.chapterStats.enrichedCount === 0;
}

export function isVisibleChapter(chapter: SkeletonChapter, showEmptyFamilies: boolean): boolean {
  return showEmptyFamilies || chapter.families.some((f) => !isEmptyFamily(f));
}

export function firstVisibleChapter(part: SkeletonPart, showEmptyFamilies: boolean): SkeletonChapter | undefined {
  return part.chapters.find((c) => isVisibleChapter(c, showEmptyFamilies));
}
