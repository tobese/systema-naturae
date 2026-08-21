// Mirrors the relevant subset of shared/src/types.ts's TaxonNode, plus the
// chapterStats annotation extractSlice.ts adds. Kept local (not imported via
// @shared) since the book's node shape is a filtered/annotated view, not the
// raw TaxonNode the rest of the portal uses.
export interface BookNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  description?: string;
  distribution?: string;
  namedAfter?: string;
  continents?: string[];
  subspeciesCount?: number;
  extinct?: boolean;
  fossil?: boolean;
  sourcedFrom?: string;
  familySlug?: string;
  appSlug?: string;
  notableMembers?: string[];
  speciesCount?: number;
  children?: BookNode[];
  speciesList?: BookNode[];
  chapterStats?: { enrichedCount: number; speciesCount: number };
  imageUrl?: string;
  iucnStatus?: string;
}

// A small per-order sidecar merged onto the portal's real order file at
// decoration time (see src/lib/decorateChapter.ts) - book-view's own data,
// never duplicating the species tree itself. See
// experiments/book-view/README.md "Data architecture".
export interface ChapterExtensions {
  // Present only for curated Parts (Mammalia, Chondrichthyes, Reptilia).
  // Absent (undefined) means "include every family" - Aves' case.
  includeFamilySlugs?: string[];
  // Keyed by species scientific name (matches shared/data/wiki-images.json).
  images: Record<string, { imageUrl?: string; iucnStatus?: string }>;
  // Keyed by familySlug.
  chapterStats: Record<string, { enrichedCount: number; speciesCount: number }>;
  // Keyed by familySlug - hand-written (familyIntros.ts) or LLM-enriched
  // prose for the one rank the portal doesn't yet carry a description for.
  familyDescriptions: Record<string, string>;
}

export interface SkeletonFamily {
  name: string;
  commonName?: string;
  familySlug: string;
  speciesCount: number;
  chapterStats?: { enrichedCount: number; speciesCount: number };
}

export interface SkeletonChapter {
  title: string;
  orderFile: string;
  orderName: string;
  kingdom: "Animalia" | "Plantae";
  families: SkeletonFamily[];
}

export interface CollageEntry {
  name: string;
  commonName?: string;
  imageUrl: string;
}

export interface SkeletonPart {
  title: string;
  className: string;
  kingdom: "Animalia" | "Plantae";
  // Class-level intro paragraph, sourced from taxonomy.json's CLASS
  // description (see scripts/enrichHigherRanksFromWikipedia.ts) - absent for
  // classes the enrichment pass couldn't find a Wikipedia article for.
  description?: string;
  // A capped, evenly-sampled set of image-bearing, real-description species
  // from across the whole class - see extractSlice.ts's collectCollageCandidates.
  collage?: CollageEntry[];
  chapters: SkeletonChapter[];
}

// Kingdom membership lives per-part/per-chapter (see above) rather than as a
// single top-level field, now that the book spans more than one kingdom.
export interface BookSkeleton {
  parts: SkeletonPart[];
}

export interface ChapterDoc {
  title: string;
  orderName: string;
  description: string;
  families: BookNode[];
}
