import { useMemo } from "react";
import type { TaxonNode, ColorTheme } from "@shared/types";
import { PORTAL_THEME } from "../colors";
import { COLOR_REGISTRY } from "../colorRegistry";

// Prune FAMILY nodes' children so only the focused family shows species.
// Non-focused FAMILY nodes appear as leaves.
function pruneTree(
  node: TaxonNode,
  focusedFamilyId: string | null,
  expandedSubspeciesIds: Set<string>,
  expandedBreedIds: Set<string>,
): TaxonNode {
  if (node.rank === "FAMILY") {
    if (!focusedFamilyId || node.id !== focusedFamilyId) {
      const { children: _c, ...rest } = node;
      return rest as TaxonNode;
    }
    // Focused family: recurse with subspecies/breed collapse
    return {
      ...node,
      children: node.children?.map(c =>
        collapseSpeciesLevel(c, expandedSubspeciesIds, expandedBreedIds)
      ),
    };
  }
  if (!node.children) return node;
  return {
    ...node,
    children: node.children.map(c =>
      pruneTree(c, focusedFamilyId, expandedSubspeciesIds, expandedBreedIds)
    ),
  };
}

// Within a focused family's subtree: collapse subspecies and breeds by default.
function collapseSpeciesLevel(
  node: TaxonNode,
  expandedSubspeciesIds: Set<string>,
  expandedBreedIds: Set<string>,
): TaxonNode {
  if (node.rank === "SPECIES") {
    const allSubspecies = node.children?.every(c => c.rank === "SUBSPECIES") ?? false;
    const hasBreeds = node.children?.some(c => c.rank === "BREED_GROUP") ?? false;

    if (allSubspecies && !expandedSubspeciesIds.has(node.id)) {
      const { children: _c, ...rest } = node;
      return rest as TaxonNode;
    }
    if (hasBreeds && !expandedBreedIds.has(node.id)) {
      const { children: _c, ...rest } = node;
      return rest as TaxonNode;
    }
    // Species with mixed children (subspecies + breed groups) - handle per type
    if (node.children) {
      return {
        ...node,
        children: node.children.map(c =>
          collapseSpeciesLevel(c, expandedSubspeciesIds, expandedBreedIds)
        ),
      };
    }
    return node;
  }
  if (!node.children) return node;
  return {
    ...node,
    children: node.children.map(c =>
      collapseSpeciesLevel(c, expandedSubspeciesIds, expandedBreedIds)
    ),
  };
}

function walkFind(node: TaxonNode, id: string): TaxonNode | null {
  if (node.id === id) return node;
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
}

function buildHighlightIds(root: TaxonNode, continent: string): Set<string> {
  const ids = new Set<string>();
  function walk(n: TaxonNode) {
    if (n.continents?.includes(continent)) ids.add(n.id);
    n.children?.forEach(walk);
  }
  walk(root);
  return ids;
}

function mergeThemes(base: ColorTheme, family: ColorTheme): ColorTheme {
  return {
    subfamilyColors: { ...base.subfamilyColors, ...family.subfamilyColors },
    lineageColors: { ...base.lineageColors, ...family.lineageColors },
    breedGroupColor: family.breedGroupColor,
    hybridColor: family.hybridColor,
    coatTypeColor: family.coatTypeColor,
  };
}

export function useUnifiedTree(
  annotatedData: TaxonNode,
  focusedFamilyId: string | null,
  expandedSubspeciesIds: Set<string>,
  expandedBreedIds: Set<string>,
  highlightedContinent: string | null,
): {
  treeData: TaxonNode;
  colorTheme: ColorTheme;
  highlightedNodeIds: Set<string> | null;
  findNodeById: (id: string) => TaxonNode | null;
} {
  const treeData = useMemo(
    () => pruneTree(annotatedData, focusedFamilyId, expandedSubspeciesIds, expandedBreedIds),
    [annotatedData, focusedFamilyId, expandedSubspeciesIds, expandedBreedIds],
  );

  const colorTheme = useMemo<ColorTheme>(() => {
    if (!focusedFamilyId) return PORTAL_THEME;
    const familyNode = walkFind(annotatedData, focusedFamilyId);
    const slug = familyNode?.familySlug;
    if (!slug || !COLOR_REGISTRY[slug]) return PORTAL_THEME;
    return mergeThemes(PORTAL_THEME, COLOR_REGISTRY[slug]);
  }, [annotatedData, focusedFamilyId]);

  const highlightedNodeIds = useMemo<Set<string> | null>(() => {
    if (!highlightedContinent || !focusedFamilyId) return null;
    const familyNode = walkFind(annotatedData, focusedFamilyId);
    if (!familyNode) return null;
    return buildHighlightIds(familyNode, highlightedContinent);
  }, [annotatedData, focusedFamilyId, highlightedContinent]);

  const findNodeById = useMemo(
    () => (id: string) => walkFind(annotatedData, id),
    [annotatedData],
  );

  return { treeData, colorTheme, highlightedNodeIds, findNodeById };
}
