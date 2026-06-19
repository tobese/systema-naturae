import { useMemo } from "react";
import type { TaxonNode } from "@shared/types";

export interface SpeciesOfTheDay {
  id: string;
  name: string;
  commonName?: string;
  description?: string;
  continents?: string[];
  subspeciesCount?: number;
  namedAfter?: string;
  familySlug: string;
}

function collectSpecies(node: TaxonNode, out: SpeciesOfTheDay[]) {
  if (node.rank === "SPECIES" && (node as any).familySlug) {
    out.push({
      id: node.id,
      name: node.name,
      commonName: node.commonName,
      description: (node as any).description,
      continents: (node as any).continents,
      subspeciesCount: (node as any).subspeciesCount,
      namedAfter: (node as any).namedAfter,
      familySlug: (node as any).familySlug,
    });
  }
  for (const child of node.children ?? []) collectSpecies(child, out);
}

function dateToSeed(dateStr: string): number {
  let h = 0;
  for (const c of dateStr) h = (Math.imul(31, h) + c.charCodeAt(0)) | 0;
  return Math.abs(h);
}

export function useSpeciesOfTheDay(root: TaxonNode): SpeciesOfTheDay | null {
  return useMemo(() => {
    const species: SpeciesOfTheDay[] = [];
    collectSpecies(root, species);
    if (species.length === 0) return null;
    const d = new Date();
    const dateStr = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    const seed = dateToSeed(dateStr);
    return species[seed % species.length];
  }, [root]);
}
