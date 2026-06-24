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
  namedAfter?: string;
  iucnStatus?: string;
  extinct?: boolean;
  children?: TaxonNode[];
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
  coatTypeColor?: string;
  classPalette?: ClassPalette;
}
