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
  children?: TaxonNode[];
}

export interface ColorTheme {
  subfamilyColors: Record<string, string>;
  lineageColors: Record<string, string>;
  breedGroupColor: string;
  hybridColor: string;
  coatTypeColor?: string;
}
