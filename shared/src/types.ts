export interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  lineage?: string;
  origin?: string;
  subspeciesCount?: number;
  hybridParents?: [string, string];
  wildParentId?: string;
  wildParentName?: string;
  coatType?: string;
  continents?: string[];
  accepted?: boolean;
  familySlug?: string;
  className?: string;
  orderName?: string;
  description?: string;
  /** Native geographic range as curated text (e.g. from POWO taxonRemarks),
   *  e.g. "E. Bolivia to WC. Brazil and N. Argentina". */
  distribution?: string;
  namedAfter?: string;
  iucnStatus?: string;
  extinct?: boolean;
  /** Known only from the fossil record (never observed alive by humans).
   *  Distinct from `extinct`, which marks taxa recorded in human history
   *  that no longer exist. */
  fossil?: boolean;
  sourcedFrom?: string;
  /** Family-level enrichment coverage: "full" (all species enriched),
   *  "partial" (some), or "empty" (none). Set on FAMILY nodes. */
  enrichmentStatus?: "full" | "partial" | "empty";
  children?: TaxonNode[];
  speciesList?: TaxonNode[];
  rankCounts?: Record<string, number>;
  _dataFile?: string;
  _familyCount?: number;
  _speciesCount?: number;
}

export interface ClassPalette {
  base: Record<string, string>;
  orders: Record<string, string>;
}

export interface ColorTheme {
  subfamilyColors: Record<string, string>;
  lineageColors: Record<string, string>;
  breedGroupColor: string;
  hybridColor: string;
  appSlug?: string;
  className?: string;
  orderName?: string;
  name?: string;
  mainColor?: string;
  coatTypeColor?: string;
  classPalette?: ClassPalette;
}
