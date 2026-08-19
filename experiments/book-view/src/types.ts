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
  speciesCount?: number;
  children?: BookNode[];
  speciesList?: BookNode[];
  chapterStats?: { enrichedCount: number; speciesCount: number };
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
  families: SkeletonFamily[];
}

export interface SkeletonPart {
  title: string;
  className: string;
  chapters: SkeletonChapter[];
}

export interface BookSkeleton {
  kingdom: string;
  parts: SkeletonPart[];
}

export interface ChapterDoc {
  title: string;
  orderName: string;
  description: string;
  families: BookNode[];
}
