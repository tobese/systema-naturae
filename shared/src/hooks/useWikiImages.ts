/**
 * useWikiImages — looks up cached Wikidata image data for a species binomial.
 *
 * Source of truth: `shared/data/wiki-images.json`, populated by
 * `scripts/fetchWikidataImages.ts` (SPARQL batch fetcher).
 *
 * Returns synthesized Commons URLs so consumers can drop the values straight
 * into `<img src>`. Filenames in the cache are bare Commons titles like
 * `Lion (Panthera leo) IUCN range 2023.svg` — we route them through
 * `Special:FilePath` which redirects to the actual upload URL and supports a
 * `?width=` thumbnail parameter.
 */
import { useEffect, useState } from "react";

// Loaded lazily via fetch() (see loadCache). Importing the JSON directly as a
// module statically inlines ~43MB / ~148k entries into the JS graph above App,
// which made Vite serialize a ~198MB ESM module and block first paint in dev for
// 60–90s. Importing the *URL* instead keeps first paint instant; the data is
// fetched on first use (non-critical: only portrait / range map / IUCN badge).
import imagesUrl from "../../data/wiki-images.json?url";

export interface WikiImageData {
  qid: string;
  /** Main image (P18) filename on Commons, raw — e.g. `Lion in masai mara.jpg` */
  imageFile?: string;
  /** Range map (P181) filenames on Commons, in Wikidata order (often IUCN-derived first) */
  rangeMapFiles?: string[];
  /** Commons category (P373), e.g. `Panthera leo` */
  commonsCat?: string;
  /** IUCN Red List code: `EX`, `EW`, `CR`, `EN`, `VU`, `NT`, `LC`, `DD`, `NE` */
  iucnStatus?: string;
}

export interface WikiImages {
  portrait?: string;
  rangeMap?: string;
  iucnStatus?: string;
  qid?: string;
  commonsCat?: string;
  raw?: WikiImageData;
}

interface RawEntry {
  qid: string;
  image?: string;
  rangeMaps?: string[];
  commonsCat?: string;
  iucnStatus?: string;
  fetchedAt: string;
}

let cache: Record<string, RawEntry> | null = null;
let cachePromise: Promise<Record<string, RawEntry>> | null = null;

/** Fetch the sidecar JSON once, memoized across all call sites. */
function loadCache(): Promise<Record<string, RawEntry>> {
  if (!cachePromise) {
    cachePromise = fetch(imagesUrl)
      .then((r) => r.json() as Promise<Record<string, RawEntry>>)
      .then((data) => {
        cache = data;
        return data;
      });
  }
  return cachePromise;
}

// Eagerly start the fetch at module load (async, non-blocking — does not delay
// first paint, unlike the old static import). By the time a user opens a species
// panel, the ~43MB sidecar is normally resident, so the cached Wikidata portrait
// is available synchronously again — keeping the species image instant.
loadCache();

const COMMONS_BASE = "https://commons.wikimedia.org/wiki/Special:FilePath/";

/** Build a Commons thumbnail URL from a bare filename. */
export function commonsThumb(filename: string, width = 600): string {
  return `${COMMONS_BASE}${encodeURIComponent(filename)}?width=${width}`;
}

/** Strip trailing authority from a scientific name, keeping only genus + species epithet. */
function stripAuthority(name: string): string {
  // If it's already a bare binomial (no authority), return as-is
  const parts = name.trim().split(/\s+/);
  if (parts.length <= 2) return name.trim();
  // Take first two words (genus + species epithet) and ignore author citation
  return parts.slice(0, 2).join(" ");
}

/** Returns null if the binomial isn't in the cache or has no useful data. */
export function useWikiImages(binomial: string | null | undefined): WikiImages | null {
  const [, force] = useState(0);
  useEffect(() => {
    if (!cache) {
      loadCache().then(() => force((n) => n + 1));
    }
  }, [binomial]);

  if (!cache || !binomial) return null;
  // Try exact match first; fall back to stripped binomial (handles authority suffixes)
  let entry = cache[binomial];
  if (!entry || !entry.qid) {
    const bare = stripAuthority(binomial);
    if (bare !== binomial) entry = cache[bare];
  }
  if (!entry || !entry.qid) return null;

  const portrait = entry.image ? commonsThumb(entry.image, 600) : undefined;
  const rangeMap = entry.rangeMaps && entry.rangeMaps.length > 0
    ? commonsThumb(entry.rangeMaps[0], 800)
    : undefined;

  if (!portrait && !rangeMap && !entry.iucnStatus) return null;

  return {
    portrait,
    rangeMap,
    iucnStatus: entry.iucnStatus,
    qid: entry.qid,
    commonsCat: entry.commonsCat,
    raw: {
      qid: entry.qid,
      imageFile: entry.image,
      rangeMapFiles: entry.rangeMaps,
      commonsCat: entry.commonsCat,
      iucnStatus: entry.iucnStatus,
    },
  };
}

/** Total count of cached entries (for debug / coverage display). */
export function wikiImagesCacheSize(): number {
  return cache ? Object.keys(cache).length : 0;
}
