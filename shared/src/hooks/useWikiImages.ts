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
import imagesCacheRaw from "../../data/wiki-images.json";

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

const cache = imagesCacheRaw as Record<string, RawEntry>;

const COMMONS_BASE = "https://commons.wikimedia.org/wiki/Special:FilePath/";

/** Build a Commons thumbnail URL from a bare filename. */
export function commonsThumb(filename: string, width = 600): string {
  return `${COMMONS_BASE}${encodeURIComponent(filename)}?width=${width}`;
}

/** Returns null if the binomial isn't in the cache or has no useful data. */
export function useWikiImages(binomial: string | null | undefined): WikiImages | null {
  if (!binomial) return null;
  const entry = cache[binomial];
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
  return Object.keys(cache).length;
}
