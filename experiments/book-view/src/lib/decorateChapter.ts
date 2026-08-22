import type { BookNode, ChapterDoc, ChapterExtensions } from "../types";

// Some enrichFromWikipedia.ts extracts are corrupted leftover MediaWiki
// markup instead of real prose - category links, raw infobox templates
// (disproportionately common on fossil/extinct species whose articles open
// with a taxobox before any prose), or article redirects. No usable
// sentence to salvage in any of these; drop the description so the UI's
// existing stub-species fallback handles it honestly instead of rendering
// raw wikitext.
const CORRUPTION_MARKERS = ["Category:", "{{", "}}", "#REDIRECT"];

function isCorrupted(description: string): boolean {
  return CORRUPTION_MARKERS.some((m) => description.includes(m));
}

function decorateNode(node: BookNode, extensions: ChapterExtensions): void {
  if (node.description && isCorrupted(node.description)) {
    node.description = undefined;
  }
  if (node.rank === "SPECIES") {
    const image = extensions.images[node.name];
    if (image?.imageUrl) node.imageUrl = image.imageUrl;
    if (image?.iucnStatus) node.iucnStatus = image.iucnStatus;
  }
  if (node.rank === "FAMILY" && node.familySlug) {
    const stats = extensions.chapterStats[node.familySlug];
    if (stats) node.chapterStats = stats;
    const intro = extensions.familyDescriptions[node.familySlug];
    if (intro) node.description = intro;
  }
  for (const child of node.children ?? []) decorateNode(child, extensions);
  for (const s of node.speciesList ?? []) decorateNode(s, extensions);
}

// Finds every FAMILY node in the order tree, honoring includeFamilySlugs
// when present (curated Parts) or every family found (Aves - no whitelist).
// Doesn't descend into a matched family looking for nested families.
function findFamilies(order: BookNode, includeFamilySlugs: string[] | undefined): BookNode[] {
  const found: BookNode[] = [];
  const walk = (node: BookNode) => {
    if (node.rank === "FAMILY" && node.familySlug) {
      if (!includeFamilySlugs || includeFamilySlugs.includes(node.familySlug)) {
        found.push(node);
      }
      return;
    }
    for (const child of node.children ?? []) walk(child);
  };
  walk(order);
  if (!includeFamilySlugs) return found; // tree-encounter order
  // preserve whitelist order, not tree-encounter order
  return includeFamilySlugs
    .map((slug) => found.find((f) => f.familySlug === slug))
    .filter((f): f is BookNode => Boolean(f));
}

// Merges a small extensions sidecar onto the portal's real, unmodified
// order tree - client-side, so the base species-tree data is never
// duplicated into book-view's own repo. See README.md "Data architecture".
export function decorateChapter(
  order: BookNode,
  extensions: ChapterExtensions,
  chapterTitle: string,
  chapterOrderName: string,
): ChapterDoc {
  const families = findFamilies(order, extensions.includeFamilySlugs);
  for (const family of families) decorateNode(family, extensions);

  return {
    title: chapterTitle,
    orderName: chapterOrderName,
    description: order.description ?? "",
    families,
  };
}
