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

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "../../..");
const ORDERS_DIR = join(REPO_ROOT, "portal/public/data/kingdoms/animalia/orders");
const GAP_REPORT_PATH = join(REPO_ROOT, "portal/data/gap-report.json");
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

// Part (Class) → Chapter (Order, numbered continuously within the Part) →
// whitelisted Family slugs, or "ALL" for every family in the order. All
// four Parts currently use "ALL" - see allFamilyChapters() below - now that
// every class in this book has good enough class-wide Wikipedia coverage
// to skip hand-curation. A future Part with genuinely patchy coverage
// should go back to an explicit familySlugs whitelist instead.
// Builds a "every family in every listed order" chapter set - used for
// classes whose Wikipedia coverage is good enough class-wide to skip
// hand-curation. orderFile normally derives orderName by title-casing
// (ARTIODACTYLA -> Artiodactyla); pass nameOverrides for the rare order
// whose file name doesn't match its taxon name 1:1 (e.g. Squamata's order
// file is SQUAMATA_ORDER.json, a naming collision elsewhere in the
// taxonomy).
function allFamilyChapters(
  orderFiles: string[],
  nameOverrides: Record<string, string> = {},
): { orderFile: string; orderName: string; title: string; familySlugs: "ALL" }[] {
  return orderFiles.map((orderFile, i) => {
    const orderName = nameOverrides[orderFile] ?? orderFile[0] + orderFile.slice(1).toLowerCase();
    return { orderFile, orderName, title: `Chapter ${i + 1} — ${orderName}`, familySlugs: "ALL" as const };
  });
}

const PARTS: {
  className: string;
  title: string;
  chapters: { orderFile: string; orderName: string; title: string; familySlugs: string[] | "ALL" }[];
}[] = [
  {
    className: "Mammalia",
    title: "Part I — Mammalia",
    // Every order, every family - Mammalia's Wikipedia coverage (61.3% of
    // all species class-wide, per gap-report.json - even better than
    // Aves') is good enough to skip hand-curation entirely, same reasoning
    // as the other Parts below.
    chapters: allFamilyChapters([
      "ARTIODACTYLA", "CARNIVORA", "CETACEA", "CHIROPTERA", "CINGULATA",
      "DASYUROMORPHIA", "DIDELPHIMORPHIA", "DIPROTODONTIA", "EULIPOTYPHLA",
      "LAGOMORPHA", "MONOTREMATA", "PERISSODACTYLA", "PHOLIDOTA", "PILOSA",
      "PRIMATES", "PROBOSCIDEA", "RODENTIA",
    ]),
  },
  {
    className: "Aves",
    title: "Part II — Aves",
    // Every order, every family - Aves' Wikipedia coverage (45.6% of all
    // species class-wide, per gap-report.json) is good enough to skip
    // hand-curation entirely.
    chapters: allFamilyChapters([
      "ACCIPITRIFORMES", "ANSERIFORMES", "APODIFORMES", "APTERYGIFORMES",
      "BUCEROTIFORMES", "CAPRIMULGIFORMES", "CARIAMIFORMES", "CASUARIIFORMES",
      "CHARADRIIFORMES", "COLIIFORMES", "COLUMBIFORMES", "CORACIIFORMES",
      "CUCULIFORMES", "EURYPYGIFORMES", "FALCONIFORMES", "GALLIFORMES",
      "GAVIIFORMES", "GRUIFORMES", "LEPTOSOMIFORMES", "MUSOPHAGIFORMES",
      "PASSERIFORMES", "PELECANIFORMES", "PHAETHONTIFORMES",
      "PHOENICOPTERIFORMES", "PICIFORMES", "PODICIPEDIFORMES",
      "PROCELLARIIFORMES", "PSITTACIFORMES", "PTEROCLIFORMES", "RHEIFORMES",
      "SPHENISCIFORMES", "STRIGIFORMES", "STRUTHIONIFORMES", "SULIFORMES",
      "TINAMIFORMES", "TROGONIFORMES", "UPUPIFORMES",
    ]),
  },
  {
    className: "Chondrichthyes",
    title: "Part III — Chondrichthyes",
    // Every order, every family too - only 7 families total, and even the
    // least-enriched (Orectolobiformes/Myliobatiformes) are still real
    // Wikipedia-sourced content, not empty stubs.
    chapters: allFamilyChapters([
      "CARCHARHINIFORMES", "LAMNIFORMES", "MYLIOBATIFORMES", "ORECTOLOBIFORMES",
    ]),
  },
  {
    className: "Reptilia",
    title: "Part IV — Reptilia",
    // Every order, every family - Reptilia's class-wide coverage (71.3% of
    // ~8,100 species) is the best of any Part in this book.
    chapters: allFamilyChapters(
      ["CROCODYLIA", "RHYNCHOCEPHALIA", "SQUAMATA_ORDER", "TESTUDINES"],
      { SQUAMATA_ORDER: "Squamata" },
    ),
  },
];

function readOrderFile(orderFile: string): TaxonNode {
  return JSON.parse(readFileSync(join(ORDERS_DIR, `${orderFile}.json`), "utf-8"));
}

function loadGapStats(): Map<string, GapRow> {
  const rows: GapRow[] = JSON.parse(readFileSync(GAP_REPORT_PATH, "utf-8"));
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

function main() {
  const gapStats = loadGapStats();
  const wikiImages = loadWikiImages();
  mkdirSync(join(OUT_DIR, "extensions"), { recursive: true });

  const skeleton = {
    kingdom: "Animalia",
    parts: [] as unknown[],
  };

  for (const part of PARTS) {
    const partSkeleton = { title: part.title, className: part.className, chapters: [] as unknown[] };

    for (const chapter of part.chapters) {
      const order = readOrderFile(chapter.orderFile);
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
        join(OUT_DIR, "extensions", `${chapter.orderFile}.json`),
        JSON.stringify(extensions, null, 2) + "\n",
      );

      partSkeleton.chapters.push({
        title: chapter.title,
        orderFile: chapter.orderFile,
        orderName: chapter.orderName,
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
          join("public/data/extensions", chapter.orderFile + ".json")
        }`,
      );
    }

    skeleton.parts.push(partSkeleton);
  }

  writeFileSync(join(OUT_DIR, "book-skeleton.json"), JSON.stringify(skeleton, null, 2) + "\n");
  console.log(`\nWrote ${join("public/data", "book-skeleton.json")}`);
}

main();
