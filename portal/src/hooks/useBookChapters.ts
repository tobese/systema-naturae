import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { BookNode, BookSkeleton, ChapterDoc, ChapterExtensions, SkeletonChapter, Kingdom } from "@shared/book/types";
import { decorateChapter } from "@shared/book/lib/decorateChapter";

// The portal's Book viewMode reads the SAME generated book data as the
// standalone app (experiments/book-view) - one canonical copy under
// portal/public/data/book/, which the standalone reaches through symlinks:
//
//   book-skeleton.json          parts -> chapters, the reading order
//   extensions[-<kingdom>].json per-order sidecar: portrait images, IUCN
//                                status, chapterStats, family prose, and
//                                the curated family whitelist
//
// and the species tree itself from the per-order files buildData.ts already
// writes to public/data/kingdoms/<kingdom>/orders/. Deliberately NOT
// unified-taxonomy.json: that tree is compressed (minimally-described
// species flattened into genus-level speciesList[]), and the book needs every
// species as its own entry.

const BOOK_DIR = "book";

// Per-kingdom extensions subdirectory, mirroring the standalone's
// KINGDOM_EXTENSIONS_DIRS and portal/data/kingdom-config.json's dataSuffix.
const EXTENSIONS_DIRS: Record<string, string> = {
  animalia: "",
  plantae: "-plantae",
  fungi: "-fungi",
  chromista: "-chromista",
  protozoa: "-protozoa",
  archaea: "-archaea",
};

// The per-kingdom order files live under orders[-suffix] (kingdom-config.json).
const ORDERS_SUFFIX: Record<string, string> = {
  animalia: "",
  plantae: "-plantae",
  fungi: "-fungi",
  chromista: "-chromista",
  protozoa: "-protozoa",
  archaea: "-archaea",
};

const MAX_CACHED_CHAPTERS = 8;

export interface BookChapter {
  chapter: ChapterDoc;
  meta: SkeletonChapter;
  partTitle: string;
  partIntro: string;
  partCollage: { name: string; commonName?: string; imageUrl: string }[];
}

export function useBookChapters(kingdom: string) {
  const [skeleton, setSkeleton] = useState<BookSkeleton | null>(null);
  const [failed, setFailed] = useState(false);
  const chapterCache = useRef<Map<string, BookChapter>>(new Map());
  const inflight = useRef<Set<string>>(new Set());
  const [version, setVersion] = useState(0);
  const base = import.meta.env.BASE_URL ?? "/";

  useEffect(() => {
    let cancelled = false;
    fetch(`${base}data/${BOOK_DIR}/book-skeleton.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((s: BookSkeleton) => {
        if (!cancelled) setSkeleton(s);
      })
      .catch(() => {
        // No generated book data yet (fresh clone - run the extract step).
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [base]);

  // orderName on portal nodes is the lowercase order id stem ("carnivora");
  // the skeleton stores display case ("Carnivora"). Join case-insensitively,
  // scoped to the active kingdom - the skeleton spans every kingdom, but a
  // given portal build serves exactly one.
  const parts = useMemo(
    () => (skeleton?.parts ?? []).filter((p) => p.kingdom.toLowerCase() === kingdom),
    [skeleton, kingdom],
  );

  const chapterIndex = useMemo(
    () => new Map(parts.flatMap((p) => p.chapters).map((c) => [c.orderName.toLowerCase(), c])),
    [parts],
  );

  const partIndex = useMemo(
    () =>
      new Map(
        parts.map((p) => [
          p.kingdom.toLowerCase() + "::" + p.className,
          { title: p.title, description: p.description ?? "", collage: p.collage ?? [] },
        ]),
      ),
    [parts],
  );

  const loadChapter = useCallback(
    (orderName: string) => {
      if (!skeleton) return;
      const meta = chapterIndex.get(orderName.toLowerCase());
      if (!meta) return;
      const key = `${kingdom}:${meta.orderFile}`;
      if (chapterCache.current.has(key)) {
        setVersion((v) => v + 1);
        return;
      }
      if (inflight.current.has(key)) return;
      inflight.current.add(key);

      const suffix = EXTENSIONS_DIRS[kingdom] ?? "";
      const orderSuffix = ORDERS_SUFFIX[kingdom] ?? "";
      const extDir = suffix ? `extensions${suffix}` : "extensions";
      Promise.all([
        fetch(`${base}data/kingdoms/${kingdom}/orders${orderSuffix}/${meta.orderFile}.json`).then((r) => r.json() as Promise<BookNode>),
        fetch(`${base}data/${BOOK_DIR}/${extDir}/${meta.orderFile}.json`).then((r) => r.json() as Promise<ChapterExtensions>),
      ])
        .then(([order, extensions]) => {
          const part = skeleton.parts.find((p) => p.kingdom.toLowerCase() === kingdom && p.chapters.some((c) => c.orderFile === meta.orderFile));
          const partMeta = part ? partIndex.get(part.kingdom.toLowerCase() + "::" + part.className) : undefined;
          // Bound the cache: a chapter tree is large, and a reader clicking
          // through many orders shouldn't grow it without limit. Map preserves
          // insertion order, so the first key is the least recently loaded.
          while (chapterCache.current.size >= MAX_CACHED_CHAPTERS) {
            const oldest = chapterCache.current.keys().next();
            if (oldest.done) break;
            chapterCache.current.delete(oldest.value);
          }
          chapterCache.current.set(key, {
            chapter: decorateChapter(order, extensions, meta.title, meta.orderName),
            meta,
            partTitle: partMeta?.title ?? part?.title ?? meta.title,
            partIntro: partMeta?.description ?? part?.description ?? "",
            partCollage: partMeta?.collage ?? part?.collage ?? [],
          });
          setVersion((v) => v + 1);
        })
        .catch(() => {
          /* chapter stays uncached; the pane shows its empty state */
        })
        .finally(() => {
          inflight.current.delete(key);
        });
    },
    [skeleton, kingdom, base, chapterIndex, partIndex],
  );

  const getChapter = useCallback(
    (orderName: string): BookChapter | undefined => {
      void version; // re-run lookup whenever a load resolves
      const meta = chapterIndex.get(orderName.toLowerCase());
      if (!meta) return undefined;
      return chapterCache.current.get(`${kingdom}:${meta.orderFile}`);
    },
    [kingdom, version, chapterIndex],
  );

  return { skeleton, failed, loadChapter, getChapter };
}

export type { Kingdom };
