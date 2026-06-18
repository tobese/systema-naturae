import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORTAL_ROOT = resolve(__dirname, "..");
const NEWS_PATH = resolve(PORTAL_ROOT, "data/species-news.json");
const TAXONOMY_PATH = resolve(PORTAL_ROOT, "data/taxonomy.json");

const GBIF_BACKBONE = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c";
const IUCN_TOKEN = process.env.IUCN_TOKEN ?? "";
const FIRST_RUN_LOOKBACK_DAYS = 90;
const INCREMENTAL_LOOKBACK_DAYS = 8;
const MAX_EVENTS = 500;

// --- Types ---

interface NewsEvent {
  id: string;
  date: string;
  type: "new_species" | "extinction";
  name: string;
  commonName: string;
  familySlug: string;
  source: "GBIF" | "IUCN";
  url: string;
}

interface NewsFile {
  updatedAt: string;
  events: NewsEvent[];
}

interface TaxonNode {
  name: string;
  rank: string;
  appSlug?: string;
  children?: TaxonNode[];
}

// --- Helpers ---

function collectFamilies(node: TaxonNode, acc = new Map<string, string>()): Map<string, string> {
  if (node.rank === "FAMILY" && node.appSlug) {
    acc.set(node.name, node.appSlug); // "Felidae" -> "felidae"
  }
  for (const child of node.children ?? []) collectFamilies(child, acc);
  return acc;
}

function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms));
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url, {
    headers: { "User-Agent": "systema-naturae-bot/1.0 (github.com/tommyb/systema-naturae)" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

// --- GBIF ---

interface GbifMatchResult {
  usageKey?: number;
}

interface GbifSearchSpecies {
  key: number;
  scientificName: string;
  vernacularName?: string;
  family?: string;
  created?: string;
}

interface GbifSearchResponse {
  results: GbifSearchSpecies[];
  count: number;
  endOfRecords: boolean;
}

async function gbifFamilyKey(familyName: string): Promise<number | null> {
  try {
    const r = await fetchJSON<GbifMatchResult>(
      `https://api.gbif.org/v1/species/match?name=${encodeURIComponent(familyName)}&rank=FAMILY`,
    );
    return r.usageKey ?? null;
  } catch {
    return null;
  }
}

async function fetchNewGbifSpecies(
  familyName: string,
  familySlug: string,
  seenIds: Set<string>,
  cutoff: Date,
): Promise<NewsEvent[]> {
  const familyKey = await gbifFamilyKey(familyName);
  if (!familyKey) return [];

  const events: NewsEvent[] = [];
  let offset = 0;

  // Pages through up to 1000 species per family (sufficient for all families we track)
  while (offset < 1000) {
    const data = await fetchJSON<GbifSearchResponse>(
      `https://api.gbif.org/v1/species/search?datasetKey=${GBIF_BACKBONE}&rank=SPECIES&status=ACCEPTED&highertaxon=${encodeURIComponent(familyName)}&limit=100&offset=${offset}`,
    );

    for (const sp of data.results) {
      // Strict family match to avoid highertaxon over-matching
      if (sp.family?.toLowerCase() !== familyName.toLowerCase()) continue;
      if (!sp.created) continue;
      const created = new Date(sp.created);
      if (created < cutoff) continue;

      const id = `gbif-${sp.key}`;
      if (seenIds.has(id)) continue;

      events.push({
        id,
        date: created.toISOString().split("T")[0],
        type: "new_species",
        name: sp.scientificName,
        commonName: sp.vernacularName ?? "",
        familySlug,
        source: "GBIF",
        url: `https://www.gbif.org/species/${sp.key}`,
      });
    }

    if (data.endOfRecords) break;
    offset += 100;
    await sleep(100);
  }

  return events;
}

// --- IUCN ---

interface IucnSpecies {
  taxonid: number;
  scientific_name: string;
  main_common_name?: string;
  category: string;
  assessment_date?: string;
}

interface IucnFamilyResponse {
  result?: IucnSpecies[];
}

async function fetchIucnExtinctions(
  familyName: string,
  familySlug: string,
  seenIds: Set<string>,
  cutoff: Date,
): Promise<NewsEvent[]> {
  if (!IUCN_TOKEN) return [];
  const events: NewsEvent[] = [];

  try {
    const data = await fetchJSON<IucnFamilyResponse>(
      `https://apiv3.iucnredlist.org/api/v3/species/family/${encodeURIComponent(familyName)}?token=${IUCN_TOKEN}`,
    );

    for (const sp of data.result ?? []) {
      if (sp.category !== "EX") continue;
      const id = `iucn-EX-${sp.taxonid}`;
      if (seenIds.has(id)) continue;

      if (sp.assessment_date) {
        const assessed = new Date(sp.assessment_date);
        if (assessed < cutoff) continue;
      }

      events.push({
        id,
        date: sp.assessment_date?.split("T")[0] ?? new Date().toISOString().split("T")[0],
        type: "extinction",
        name: sp.scientific_name,
        commonName: sp.main_common_name ?? "",
        familySlug,
        source: "IUCN",
        url: `https://www.iucnredlist.org/search?query=${encodeURIComponent(sp.scientific_name)}`,
      });
    }
  } catch (e) {
    console.warn(`  IUCN error for ${familyName}:`, (e as Error).message);
  }

  return events;
}

// --- Main ---

async function main() {
  console.log("Fetching species news…\n");

  let existing: NewsFile = { updatedAt: "1970-01-01", events: [] };
  if (existsSync(NEWS_PATH)) {
    existing = JSON.parse(readFileSync(NEWS_PATH, "utf-8")) as NewsFile;
  }

  const seenIds = new Set(existing.events.map(e => e.id));
  const isFirstRun = existing.updatedAt === "1970-01-01";

  const cutoff = new Date();
  if (isFirstRun) {
    cutoff.setDate(cutoff.getDate() - FIRST_RUN_LOOKBACK_DAYS);
    console.log(`First run — looking back ${FIRST_RUN_LOOKBACK_DAYS} days (since ${cutoff.toISOString().split("T")[0]})`);
  } else {
    cutoff.setDate(cutoff.getDate() - INCREMENTAL_LOOKBACK_DAYS);
    console.log(`Incremental run — looking back ${INCREMENTAL_LOOKBACK_DAYS} days (since ${cutoff.toISOString().split("T")[0]})`);
  }

  const taxonomy = JSON.parse(readFileSync(TAXONOMY_PATH, "utf-8")) as TaxonNode;
  const families = collectFamilies(taxonomy);
  console.log(`Checking ${families.size} families\n`);

  const newEvents: NewsEvent[] = [];

  // GBIF: new species per family
  console.log("── GBIF new species ──");
  for (const [familyName, familySlug] of families) {
    process.stdout.write(`  ${familyName}… `);
    try {
      const events = await fetchNewGbifSpecies(familyName, familySlug, seenIds, cutoff);
      console.log(events.length > 0 ? `${events.length} new` : "–");
      newEvents.push(...events);
    } catch (e) {
      console.log(`error: ${(e as Error).message}`);
    }
    await sleep(150);
  }

  // IUCN: extinctions per family
  if (IUCN_TOKEN) {
    console.log("\n── IUCN extinctions ──");
    for (const [familyName, familySlug] of families) {
      process.stdout.write(`  ${familyName}… `);
      try {
        const events = await fetchIucnExtinctions(familyName, familySlug, seenIds, cutoff);
        console.log(events.length > 0 ? `${events.length} extinct` : "–");
        newEvents.push(...events);
      } catch (e) {
        console.log(`error: ${(e as Error).message}`);
      }
      await sleep(200);
    }
  } else {
    console.log("\nNo IUCN_TOKEN set — skipping extinctions");
  }

  console.log(`\n${newEvents.length} new event(s) found`);

  const allEvents = [
    ...newEvents.sort((a, b) => b.date.localeCompare(a.date)),
    ...existing.events,
  ].slice(0, MAX_EVENTS);

  const updated: NewsFile = {
    updatedAt: new Date().toISOString().split("T")[0],
    events: allEvents,
  };

  writeFileSync(NEWS_PATH, JSON.stringify(updated, null, 2));
  console.log(`Done. ${allEvents.length} total event(s) written.`);
}

main().catch(e => { console.error(e); process.exit(1); });
