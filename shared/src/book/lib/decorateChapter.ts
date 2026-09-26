import type { BookNode, ChapterDoc, ChapterExtensions } from "../types";
import { synonymTarget } from "./synonyms";
import { breedKey } from "./breedKey";

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

function decorateNode(node: BookNode, extensions: ChapterExtensions, host?: string): void {
  if (node.description && isCorrupted(node.description)) {
    node.description = undefined;
  }
  // A breed's portrait is keyed by host species as well as name, so it is
  // tracked down the walk rather than read off the node - see lib/breedKey.ts.
  if (node.rank === "SPECIES" && node.name) host = node.name;
  if (node.rank === "SPECIES" || node.rank === "BREED") {
    const key = node.rank === "BREED" ? breedKey(host, node.name) : node.name;
    const image = extensions.images[key];
    // Synonym stubs (e.g. "Felis lanea") carry no portrait under their own
    // name but their description is the accepted species' - reuse that
    // species' image + status so the row isn't a text-only orphan.
    const syn = node.rank === "SPECIES" && !image?.imageUrl ? synonymTarget(node) : null;
    const source = image ?? (syn ? extensions.images[syn] : undefined);
    if (source?.imageUrl) node.imageUrl = source.imageUrl;
    if (source?.iucnStatus) node.iucnStatus = source.iucnStatus;
  }
  if (node.rank === "FAMILY" && node.familySlug) {
    const stats = extensions.chapterStats[node.familySlug];
    if (stats) node.chapterStats = stats;
    const intro = extensions.familyDescriptions[node.familySlug];
    if (intro) node.description = intro;
  }
  for (const child of node.children ?? []) decorateNode(child, extensions, host);
  for (const s of node.speciesList ?? []) decorateNode(s, extensions, host);
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
// duplicated into either app. See experiments/book-view/README.md
// "Data architecture".
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
