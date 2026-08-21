// Builds this prototype's small per-order "extension" sidecars (portrait
// images, IUCN status, chapter stats, curated Family-level prose, and the
// curated-Parts family whitelist) plus the Contents-page skeleton. Read-only
// against the portal - never writes back to it, and no longer copies the
// portal's species-tree data itself (that's symlinked in directly via
// public/data/portal-orders, decorated client-side by src/lib/decorateChapter.ts).
// Re-run any time upstream data changes: `npm run extract-data`.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { FAMILY_INTROS } from "../src/familyIntros";
import { COLLAGE_OVERRIDES } from "../src/collageOverrides";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "../../..");

type Kingdom = "Animalia" | "Plantae";

const ORDERS_DIRS: Record<Kingdom, string> = {
  Animalia: join(REPO_ROOT, "portal/public/data/kingdoms/animalia/orders"),
  Plantae: join(REPO_ROOT, "portal/public/data/kingdoms/plantae/orders-plantae"),
};
const GAP_REPORT_PATHS: Record<Kingdom, string> = {
  Animalia: join(REPO_ROOT, "portal/data/gap-report.json"),
  Plantae: join(REPO_ROOT, "portal/data/gap-report-plantae.json"),
};
// extensions output is namespaced per kingdom (extensions/ vs
// extensions-plantae/) so adding Plantae never touches the already-verified
// Animalia sidecar files.
const EXTENSIONS_DIRS: Record<Kingdom, string> = {
  Animalia: "extensions",
  Plantae: "extensions-plantae",
};
const MANIFEST_PATHS: Record<Kingdom, string> = {
  Animalia: join(REPO_ROOT, "portal/public/data/kingdoms/animalia/order-manifest.json"),
  Plantae: join(REPO_ROOT, "portal/public/data/kingdoms/plantae/order-manifest.json"),
};
// Source of truth for CLASS-level `description` (see
// scripts/enrichHigherRanksFromWikipedia.ts, which fills these in upstream) -
// used for each Part's intro paragraph, same file taxonomy.json's ORDER
// nodes are grafted from into the order files already read via ORDERS_DIRS.
const TAXONOMY_PATHS: Record<Kingdom, string> = {
  Animalia: join(REPO_ROOT, "portal/data/taxonomy.json"),
  Plantae: join(REPO_ROOT, "portal/data/taxonomy-plantae-snippet.json"),
};
const WIKI_IMAGES_PATH = join(REPO_ROOT, "shared/data/wiki-images.json");
const OUT_DIR = join(__dirname, "../public/data");
const COMMONS_FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/";

// Same URL-construction convention as shared/src/hooks/useWikiImages.ts
// (bare Commons filenames routed through Special:FilePath, which redirects
// to the real upload and supports a ?width= thumbnail param).
function commonsThumb(filename: string, width = 480): string {
  return `${COMMONS_FILEPATH}${encodeURIComponent(filename)}?width=${width}`;
}

interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  description?: string;
  familySlug?: string;
  appSlug?: string;
  speciesCount?: number;
  children?: TaxonNode[];
  speciesList?: TaxonNode[];
}

interface GapRow {
  appSlug: string;
  speciesCount: number;
  enrichedCount: number;
}

interface WikiImageEntry {
  qid: string;
  image?: string;
  iucnStatus?: string;
}

interface ManifestEntry {
  classSlug: string;
  orderSlug: string;
}
interface KingdomManifest {
  orders: Record<string, ManifestEntry>;
}

const manifestCache: Partial<Record<Kingdom, KingdomManifest>> = {};
function loadManifest(kingdom: Kingdom): KingdomManifest {
  if (!manifestCache[kingdom]) {
    manifestCache[kingdom] = JSON.parse(readFileSync(MANIFEST_PATHS[kingdom], "utf-8"));
  }
  return manifestCache[kingdom]!;
}

// No library needed - Part numbers only ever run into the low hundreds.
function intToRoman(num: number): string {
  const table: [number, string][] = [
    [1000, "M"], [900, "CM"], [500, "D"], [400, "CD"],
    [100, "C"], [90, "XC"], [50, "L"], [40, "XL"],
    [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"],
  ];
  let n = num;
  let result = "";
  for (const [value, symbol] of table) {
    while (n >= value) {
      result += symbol;
      n -= value;
    }
  }
  return result;
}

interface PartDef {
  className: string;
  kingdom: Kingdom;
  title: string;
  description?: string;
  chapters: { orderFile: string; orderName: string; title: string; familySlugs: "ALL" }[];
}

// Walks a kingdom's taxonomy source file once, collecting each CLASS node's
// `description` keyed by lowercased name (matches order-manifest.json's
// classSlug convention). Most Animalia classes still have none (see
// scripts/enrichHigherRanksFromWikipedia.ts for the upstream fill pass);
// Plantae is already fully covered at CLASS rank.
function loadClassDescriptions(kingdom: Kingdom): Map<string, string> {
  const root: TaxonNode = JSON.parse(readFileSync(TAXONOMY_PATHS[kingdom], "utf-8"));
  const map = new Map<string, string>();
  const walk = (node: TaxonNode) => {
    if (node.rank === "CLASS" && node.description) {
      map.set(node.name.toLowerCase(), node.description);
    }
    for (const child of node.children ?? []) walk(child);
  };
  walk(root);
  return map;
}

// Generates one Part per class and one Chapter per order, straight from the
// portal's own order-manifest.json - every class with real built species
// data becomes a Part, unconditionally (no enrichment-% curation bar
// anymore; the showStubs/showEmptyFamilies options, validated last round on
// Cephalopoda/Octopoda, are what make sparse/patchy classes safe to include
// wholesale). The manifest's insertion order matches taxonomy.json's real
// class order (verified directly), so Part numbering reads in the same
// sequence as the portal's own tree. Also retires the old nameOverrides
// mechanism entirely - orderSlug already resolves every known naming
// collision (SQUAMATA_ORDER -> "squamata", PERCIFORMES_FISH ->
// "perciformes", the various ORD_-prefixed Plantae files, etc.) without
// needing a lookup table.
function buildKingdomParts(kingdom: Kingdom): PartDef[] {
  const manifest = loadManifest(kingdom);
  const classDescriptions = loadClassDescriptions(kingdom);
  const classOrder: string[] = [];
  const orderIdsByClass = new Map<string, string[]>();
  for (const [orderId, info] of Object.entries(manifest.orders)) {
    if (!orderIdsByClass.has(info.classSlug)) {
      orderIdsByClass.set(info.classSlug, []);
      classOrder.push(info.classSlug);
    }
    orderIdsByClass.get(info.classSlug)!.push(orderId);
  }

  return classOrder.map((classSlug, classIndex) => {
    const className = classSlug[0].toUpperCase() + classSlug.slice(1);
    const chapters = orderIdsByClass.get(classSlug)!.map((orderFile, chapterIndex) => {
      const orderSlug = manifest.orders[orderFile].orderSlug;
      const orderName = orderSlug[0].toUpperCase() + orderSlug.slice(1);
      return {
        orderFile,
        orderName,
        title: `Chapter ${chapterIndex + 1} — ${orderName}`,
        familySlugs: "ALL" as const,
      };
    });
    return {
      className,
      kingdom,
      title: `Part ${intToRoman(classIndex + 1)} — ${className}`,
      description: classDescriptions.get(classSlug),
      chapters,
    };
  });
}

const PARTS: PartDef[] = [...buildKingdomParts("Animalia"), ...buildKingdomParts("Plantae")];

function readOrderFile(kingdom: Kingdom, orderFile: string): TaxonNode {
  return JSON.parse(readFileSync(join(ORDERS_DIRS[kingdom], `${orderFile}.json`), "utf-8"));
}

function loadGapStats(kingdom: Kingdom): Map<string, GapRow> {
  const rows: GapRow[] = JSON.parse(readFileSync(GAP_REPORT_PATHS[kingdom], "utf-8"));
  const map = new Map<string, GapRow>();
  for (const row of rows) map.set(row.appSlug, row);
  return map;
}

function loadWikiImages(): Record<string, WikiImageEntry> {
  return JSON.parse(readFileSync(WIKI_IMAGES_PATH, "utf-8"));
}

function findFamilies(order: TaxonNode, slugs: string[] | "ALL"): TaxonNode[] {
  const found: TaxonNode[] = [];
  const walk = (node: TaxonNode) => {
    if (node.rank === "FAMILY" && node.familySlug && (slugs === "ALL" || slugs.includes(node.familySlug))) {
      found.push(node);
      return; // don't descend into a matched family looking for nested families
    }
    for (const child of node.children ?? []) walk(child);
  };
  walk(order);
  if (slugs === "ALL") return found; // tree-encounter order
  // preserve whitelist order, not tree-encounter order
  return slugs
    .map((slug) => found.find((f) => f.familySlug === slug))
    .filter((f): f is TaxonNode => Boolean(f));
}

// Collects every species scientific name under a family - used to slice
// only the relevant entries out of the 43MB wiki-images.json sidecar rather
// than shipping any of it to the browser.
function collectSpeciesNames(node: TaxonNode, out: string[]): void {
  if (node.rank === "SPECIES") out.push(node.name);
  for (const child of node.children ?? []) collectSpeciesNames(child, out);
  for (const s of node.speciesList ?? []) collectSpeciesNames(s, out);
}

interface CollageCandidate {
  name: string;
  commonName?: string;
  imageUrl: string;
}

// Collects species that are genuinely "collage-worthy" - a real (non-stub)
// description *and* a portrait image - from anywhere under a family.
// speciesList (compressed stubs) is skipped: a collage entry with a photo
// but no real description behind it isn't representative of this book's
// content.
function collectCollageCandidates(
  node: TaxonNode,
  wikiImages: Record<string, WikiImageEntry>,
  out: CollageCandidate[],
): void {
  if (node.rank === "SPECIES") {
    const entry = wikiImages[node.name];
    if (entry?.image && (node.description?.length ?? 0) > 20) {
      out.push({ name: node.name, commonName: node.commonName, imageUrl: commonsThumb(entry.image) });
    }
    return;
  }
  for (const child of node.children ?? []) collectCollageCandidates(child, wikiImages, out);
}

// Deterministic evenly-spaced sample (no randomness, so extract-data output
// stays reproducible) - avoids every collage looking like "whatever family
// happens to come first alphabetically."
function sampleEvenly<T>(items: T[], count: number): T[] {
  if (items.length <= count) return items;
  const step = items.length / count;
  const out: T[] = [];
  for (let i = 0; i < count; i++) out.push(items[Math.floor(i * step)]);
  return out;
}

const COLLAGE_SIZE = 81; // a 9x9 plate
const COLLAGE_CENTER_INDEX = 40; // row-major middle of a 9x9 grid

// Builds a Part's collage. Flagship classes with a src/collageOverrides.ts
// entry get specific species pinned at specific slots (center + pinned list)
// - everything else in the grid, and every class without an override, is
// filled by the same deterministic even-sampling as before, just at 81
// instead of 8. Pinning only actually lands `center` in the visual middle
// when the class has enough real candidates to fill every slot before it
// (true for any class this large, e.g. Mammalia's thousands of species) -
// documented rather than defended against, since a flagship override on a
// too-small class isn't a real scenario.
function buildCollage(className: string, candidates: CollageCandidate[]): CollageCandidate[] {
  const override = COLLAGE_OVERRIDES[className];
  if (!override) return sampleEvenly(candidates, COLLAGE_SIZE);

  const byName = new Map(candidates.map((c) => [c.name, c]));
  const grid: (CollageCandidate | undefined)[] = new Array(COLLAGE_SIZE).fill(undefined);
  const used = new Set<string>();

  if (override.center) {
    const c = byName.get(override.center);
    if (c) {
      grid[COLLAGE_CENTER_INDEX] = c;
      used.add(c.name);
    }
  }

  let slot = 0;
  for (const name of override.pinned ?? []) {
    const c = byName.get(name);
    if (!c || used.has(c.name)) continue;
    while (grid[slot] !== undefined) slot++;
    grid[slot] = c;
    used.add(c.name);
  }

  const remaining = candidates.filter((c) => !used.has(c.name));
  const emptySlots = grid.filter((c) => c === undefined).length;
  const filler = sampleEvenly(remaining, emptySlots);
  let fillerIndex = 0;
  for (let i = 0; i < grid.length && fillerIndex < filler.length; i++) {
    if (grid[i] === undefined) grid[i] = filler[fillerIndex++];
  }

  return grid.filter((c): c is CollageCandidate => c !== undefined);
}

function main() {
  const gapStatsByKingdom: Record<Kingdom, Map<string, GapRow>> = {
    Animalia: loadGapStats("Animalia"),
    Plantae: loadGapStats("Plantae"),
  };
  const wikiImages = loadWikiImages();
  mkdirSync(join(OUT_DIR, "extensions"), { recursive: true });
  mkdirSync(join(OUT_DIR, "extensions-plantae"), { recursive: true });

  const skeleton = {
    parts: [] as unknown[],
  };

  for (const part of PARTS) {
    const gapStats = gapStatsByKingdom[part.kingdom];
    const extensionsDir = EXTENSIONS_DIRS[part.kingdom];
    const partSkeleton = {
      title: part.title,
      className: part.className,
      kingdom: part.kingdom,
      description: part.description,
      collage: [] as CollageCandidate[],
      chapters: [] as unknown[],
    };
    const collageCandidates: CollageCandidate[] = [];

    for (const chapter of part.chapters) {
      const order = readOrderFile(part.kingdom, chapter.orderFile);
      const families = findFamilies(order, chapter.familySlugs);

      const chapterStats: Record<string, { enrichedCount: number; speciesCount: number }> = {};
      const familyDescriptions: Record<string, string> = {};
      const images: Record<string, { imageUrl?: string; iucnStatus?: string }> = {};
      let imagesAttached = 0;

      for (const family of families) {
        const slug = family.familySlug!;
        const stats = gapStats.get(slug);
        if (stats) chapterStats[slug] = { enrichedCount: stats.enrichedCount, speciesCount: stats.speciesCount };
        const intro = FAMILY_INTROS[slug];
        if (intro) familyDescriptions[slug] = intro;

        collectCollageCandidates(family, wikiImages, collageCandidates);

        const speciesNames: string[] = [];
        collectSpeciesNames(family, speciesNames);
        for (const name of speciesNames) {
          const entry = wikiImages[name];
          if (!entry?.image && !entry?.iucnStatus) continue;
          images[name] = {
            ...(entry.image ? { imageUrl: commonsThumb(entry.image) } : {}),
            ...(entry.iucnStatus ? { iucnStatus: entry.iucnStatus } : {}),
          };
          if (entry.image) imagesAttached++;
        }
      }
      if (imagesAttached > 0) {
        console.log(`    (${imagesAttached} portrait image${imagesAttached === 1 ? "" : "s"})`);
      }

      const extensions = {
        includeFamilySlugs: chapter.familySlugs === "ALL" ? undefined : chapter.familySlugs,
        images,
        chapterStats,
        familyDescriptions,
      };
      writeFileSync(
        join(OUT_DIR, extensionsDir, `${chapter.orderFile}.json`),
        JSON.stringify(extensions, null, 2) + "\n",
      );

      partSkeleton.chapters.push({
        title: chapter.title,
        orderFile: chapter.orderFile,
        orderName: chapter.orderName,
        kingdom: part.kingdom,
        families: families.map((f) => ({
          name: f.name,
          commonName: f.commonName,
          familySlug: f.familySlug,
          speciesCount: f.speciesCount,
          chapterStats: chapterStats[f.familySlug!],
        })),
      });

      console.log(
        `  ${chapter.title}: ${families.map((f) => f.familySlug).join(", ")} -> ${
          join(`public/data/${extensionsDir}`, chapter.orderFile + ".json")
        }`,
      );
    }

    partSkeleton.collage = buildCollage(part.className, collageCandidates);

    skeleton.parts.push(partSkeleton);
  }

  writeFileSync(join(OUT_DIR, "book-skeleton.json"), JSON.stringify(skeleton, null, 2) + "\n");
  console.log(`\nWrote ${join("public/data", "book-skeleton.json")}`);
}

main();
