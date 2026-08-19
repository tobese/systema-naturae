import { useState, useCallback, useRef, useEffect } from "react";
import type { BookSkeleton, ChapterDoc } from "../types";

// Mirrors portal/src/hooks/useTaxonomyLoader.ts's skeleton + on-demand-fetch +
// LRU-cache pattern, at book "chapter" (= taxonomic order) granularity. The cap
// is set above the total chapter count so it's a no-op today, but the shape is
// identical to what a full-scale book (many Parts, many Chapters) would need —
// see experiments/book-view/README.md "Scaling notes".
const MAX_CACHED_CHAPTERS = 8;

function touchLRU(arr: string[], id: string): void {
  const idx = arr.indexOf(id);
  if (idx !== -1) arr.splice(idx, 1);
  arr.push(id);
}

export function useBookData(): {
  skeleton: BookSkeleton | null;
  loading: boolean;
  loadChapter: (orderFile: string) => void;
  isChapterLoading: (orderFile: string) => boolean;
  getChapter: (orderFile: string) => ChapterDoc | undefined;
} {
  const [skeleton, setSkeleton] = useState<BookSkeleton | null>(null);
  const [loading, setLoading] = useState(true);
  const [inflightChapters, setInflightChapters] = useState<Set<string>>(new Set());
  const [cacheVersion, setCacheVersion] = useState(0);
  const chapterCache = useRef<Map<string, ChapterDoc>>(new Map());
  const accessOrder = useRef<string[]>([]);

  const base = import.meta.env.BASE_URL ?? "/";

  useEffect(() => {
    fetch(`${base}data/book-skeleton.json`)
      .then((r) => r.json())
      .then((sk: BookSkeleton) => {
        setSkeleton(sk);
        setLoading(false);
      })
      .catch((e) => {
        console.error("Failed to load book skeleton:", e);
        setLoading(false);
      });
  }, [base]);

  const loadChapter = useCallback(
    (orderFile: string) => {
      if (chapterCache.current.has(orderFile)) {
        touchLRU(accessOrder.current, orderFile);
        setCacheVersion((v) => v + 1);
        return;
      }

      setInflightChapters((prev) => new Set(prev).add(orderFile));

      fetch(`${base}data/chapters/${orderFile}.json`)
        .then((r) => r.json())
        .then((doc: ChapterDoc) => {
          if (chapterCache.current.size >= MAX_CACHED_CHAPTERS && accessOrder.current.length > 0) {
            const oldest = accessOrder.current.shift()!;
            chapterCache.current.delete(oldest);
          }
          chapterCache.current.set(orderFile, doc);
          touchLRU(accessOrder.current, orderFile);
          setCacheVersion((v) => v + 1);
          setInflightChapters((prev) => {
            const next = new Set(prev);
            next.delete(orderFile);
            return next;
          });
        })
        .catch((e) => {
          console.error(`Failed to load chapter ${orderFile}:`, e);
          setInflightChapters((prev) => {
            const next = new Set(prev);
            next.delete(orderFile);
            return next;
          });
        });
    },
    [base],
  );

  const isChapterLoading = useCallback((orderFile: string) => inflightChapters.has(orderFile), [inflightChapters]);

  const getChapter = useCallback(
    (orderFile: string) => chapterCache.current.get(orderFile),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [cacheVersion],
  );

  return { skeleton, loading, loadChapter, isChapterLoading, getChapter };
}
