import type { TaxonNode, ColorTheme } from "@shared/types";
import type { PortalNode } from "./types";

export const PORTAL_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    Mammalia:       "#C87941",
    Aves:           "#3A8090",
    Carnivora:      "#D4873A",
    Perissodactyla: "#C89050",
    Artiodactyla:   "#8B7340",
    Galliformes:    "#2E9E8C",
    Anseriformes:   "#3A6090",
  },
  breedGroupColor: "#888",
  hybridColor: "#888",
};

// Legacy version used by old portal (propagates through all descendants).
export function annotatePortalTree(node: PortalNode, className?: string, orderName?: string): PortalNode {
  const nextClass = node.rank === "CLASS" ? node.name : className;
  const nextOrder = node.rank === "ORDER" ? node.name : orderName;
  return {
    ...node,
    lineage: nextOrder ?? nextClass,
    children: node.children?.map(c => annotatePortalTree(c, nextClass, nextOrder)),
  };
}

// Family-level-aware version: stamps lineage on CLASS/ORDER/FAMILY nodes only.
// Nodes at SUBFAMILY rank and below already carry their own lineage from the family JSON.
const SPECIES_LEVEL_RANKS = new Set([
  "SUBFAMILY", "TRIBE", "GENUS", "SPECIES", "SUBSPECIES",
  "BREED_GROUP", "BREED", "HYBRID_GROUP", "HYBRID",
]);

export function annotatePortalLevels(node: TaxonNode, className?: string, orderName?: string): TaxonNode {
  const nextClass = node.rank === "CLASS" ? node.name : className;
  const nextOrder = node.rank === "ORDER" ? node.name : orderName;
  const lineage = SPECIES_LEVEL_RANKS.has(node.rank) ? node.lineage : (nextOrder ?? nextClass);
  return {
    ...node,
    lineage,
    children: node.children?.map(c => annotatePortalLevels(c, nextClass, nextOrder)),
  };
}
