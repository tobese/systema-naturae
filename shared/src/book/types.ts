// Mirrors the relevant subset of shared/src/types.ts's TaxonNode, plus the
// chapterStats annotation extractSlice.ts adds. Deliberately a separate type
// from TaxonNode: the book's node shape is a filtered/annotated view (see
// decorateChapter.ts), not the raw node the graph and its other consumers use.
// Lives in shared/src/book/ so the standalone app (experiments/book-view) and
// the portal's Book viewMode render from one implementation.
export interface BookNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  description?: string;
  distribution?: string;
  namedAfter?: string;
  // Populated on nearly every species (genus/group label, used for tree
  // coloring elsewhere in the portal) - book-view only surfaces it for
  // HYBRID nodes, where it's parentage in "A ♂ × B ♀" form instead (see
  // SpeciesEntry.tsx's isHybrid check; e.g. Equidae's Hybrids).
  lineage?: string;
  // BREED nodes only - country/region of origin (see SpeciesEntry.tsx's
  // breedGroups rendering) and coat length (longhair/shorthair, etc.).
  origin?: string;
  coatType?: string;
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
// decoration time (see lib/decorateChapter.ts) - the book's own data, never
// duplicating the species tree itself. See
// experiments/book-view/README.md "Data architecture".
export interface ChapterExtensions {
  // Present only for curated Parts (Mammalia, Chondrichthyes, Reptilia).
  // Absent (undefined) means "include every family" - Aves' case.
  includeFamilySlugs?: string[];
  // Keyed by species scientific name (matches shared/data/wiki-images.json) and
  // by breed display name (matches shared/data/breed-images.json).
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

export type Kingdom = "Animalia" | "Plantae" | "Fungi" | "Chromista" | "Protozoa" | "Archaea";

export interface SkeletonChapter {
  title: string;
  orderFile: string;
  orderName: string;
  kingdom: Kingdom;
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
  kingdom: Kingdom;
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
