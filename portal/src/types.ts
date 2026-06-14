import type { TaxonNode } from "@shared/types";

export interface PortalNode extends TaxonNode {
  appSlug?: string;
  speciesCount?: number;
  speciesTotal?: number;
  notableMembers?: string[];
  taxonomicNote?: string;
  children?: PortalNode[];
}
