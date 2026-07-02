import { useMemo } from "react";
import type { TaxonNode, ColorTheme } from "@shared/types";
import { PORTAL_THEME, buildClassPalette } from "../colors";
import { COLOR_REGISTRY } from "../colorRegistry";

const CLASS_PALETTE = buildClassPalette();

// Overview mode: collapse all families to leaf nodes (no species shown).
// Focused mode: return only the focused family subtree (rooted at the family).
function pruneTree(
  node: TaxonNode | null | undefined,
  focusedFamilyId: string | null,
  focusedClassId: string | null,
  expandedSubspeciesIds: Set<string>,
  expandedBreedIds: Set<string>,
): TaxonNode | null {
  if (!node) return null;
  if (!focusedFamilyId) {
    if (!node.children) return node;

    // Overview mode: strip children of ORDER so the graph only renders
    // KINGDOM → PHYLUM → CLASS → ORDER. Families and lower ranks become
    // reachable only when a class or family is focused.
    // (Don't strip when a class is focused — FamilyTree handles class-focus pruning.)
    if (node.rank === "ORDER" && !focusedClassId) {
      let familyCount = 0;
      for (const c of node.children) {
        if (c.rank === "FAMILY") familyCount++;
      }
      return { ...node, children: undefined, _familyCount: familyCount } as unknown as TaxonNode;
    }

    const pruned = node.children.map(c => pruneTree(c, null, focusedClassId, expandedSubspeciesIds, expandedBreedIds)).filter((c): c is TaxonNode => c !== null);
    let familyCount = 0;
    if (node.rank === "KINGDOM" || node.rank === "PHYLUM" || node.rank === "CLASS") {
      function walkCounts(n: TaxonNode): void {
        for (const c of n.children ?? []) {
          if (c.rank === "FAMILY") familyCount++;
          walkCounts(c);
        }
      }
      walkCounts(node);
    }
    return { ...node, children: pruned, _familyCount: familyCount } as unknown as TaxonNode;
  }

  // Focused mode: return only the focused family subtree (rooted at the family).
  function find(n: TaxonNode): TaxonNode | null {
    if (n.rank === "FAMILY") {
      if (n.id !== focusedFamilyId) return null;
      return {
        ...n,
        children: n.children?.map(c =>
          collapseSpeciesLevel(c, expandedSubspeciesIds, expandedBreedIds)
        ),
      };
    }
    for (const c of n.children ?? []) {
      const found = find(c);
      if (found) return found;
    }
    return null;
  }
  return find(node);
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
  if (node.speciesList) {
    const foundSp = node.speciesList.find(s => s.id === id);
    if (foundSp) return foundSp;
  }
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
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
  annotatedData: TaxonNode | null,
  focusedFamilyId: string | null,
  focusedClassId: string | null,
  expandedSubspeciesIds: Set<string>,
  expandedBreedIds: Set<string>,
  highlightedContinent: string | null,
  highlightWikipedia: boolean,
): {
  treeData: TaxonNode;
  colorTheme: ColorTheme;
  highlightedNodeIds: Set<string> | null;
  findNodeById: (id: string) => TaxonNode | null;
} {
  const treeData = useMemo(
    () => (annotatedData ? (pruneTree(annotatedData, focusedFamilyId, focusedClassId, expandedSubspeciesIds, expandedBreedIds) ?? annotatedData) : null) as unknown as TaxonNode,
    [annotatedData, focusedFamilyId, focusedClassId, expandedSubspeciesIds, expandedBreedIds],
  );

  const colorTheme = useMemo<ColorTheme>(() => {
    let theme = PORTAL_THEME;
    if (focusedFamilyId && annotatedData) {
      const familyNode = walkFind(annotatedData, focusedFamilyId);
      const slug = familyNode?.familySlug;
      if (slug && COLOR_REGISTRY[slug]) {
        theme = mergeThemes(PORTAL_THEME, COLOR_REGISTRY[slug]);
      }
    }
    return { ...theme, classPalette: CLASS_PALETTE };
  }, [annotatedData, focusedFamilyId]);

  const highlightedNodeIds = useMemo<Set<string> | null>(() => {
    if (!focusedFamilyId || !annotatedData) return null;
    const familyNode = walkFind(annotatedData, focusedFamilyId);
    if (!familyNode) return null;

    const ids = new Set<string>();

    if (highlightedContinent) {
      const continent = highlightedContinent;
      function walkContinent(n: TaxonNode) {
        if (n.continents?.includes(continent)) ids.add(n.id);
        n.children?.forEach(walkContinent);
      }
      walkContinent(familyNode);
    }

    if (highlightWikipedia) {
      function walkWiki(n: TaxonNode) {
        if (n.sourcedFrom === "wikipedia") ids.add(n.id);
        n.children?.forEach(walkWiki);
      }
      walkWiki(familyNode);
    }

    if (ids.size === 0) return null;
    return ids;
  }, [annotatedData, focusedFamilyId, highlightedContinent, highlightWikipedia]);

  const findNodeById = useMemo(
    () => (id: string) => annotatedData ? walkFind(annotatedData, id) : null,
    [annotatedData],
  );

  return { treeData, colorTheme, highlightedNodeIds, findNodeById };
}
