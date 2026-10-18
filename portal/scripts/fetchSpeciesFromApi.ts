import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import { gunzipSync } from "zlib";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

// Kingdom awareness (mirrors buildData.ts): SN_KINGDOM selects which taxonomy
// file this import reads/writes, so fungi/plantae imports never touch animalia.
interface KingdomConfig { label: string; input: string; rootDir: string; dataSuffix: string; colorRegistry: string; }
const SN_KINGDOM = process.env.SN_KINGDOM || "";
let _kcfg: KingdomConfig | undefined;
{
  const p = resolve(portalRoot, "data/kingdom-config.json");
  if (existsSync(p)) _kcfg = (JSON.parse(readFileSync(p, "utf-8")) as { kingdoms: Record<string, KingdomConfig> }).kingdoms[SN_KINGDOM];
}
const TAXONOMY_INPUT = _kcfg?.input ?? process.env.SN_INPUT ?? "data/taxonomy.json";
const TAXONOMY_PATH = resolve(portalRoot, TAXONOMY_INPUT);
const KINGDOM = SN_KINGDOM || "animalia";

// When set, species go through services/importwrite instead of a direct
// writeFileSync — the service serializes concurrent writers per family and
// merges duplicate species instead of leaving two importer runs to collide
// in a later git merge. See services/importwrite/README.md.
const IMPORTWRITE_URL = process.env.IMPORTWRITE_URL || "";

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";

const RATE_LIMIT_DELAY = 150; // ms between Wikipedia calls

/**
 * Per-dataset record IDs for a species — which dataset's record a name/ID
 * came from, keyed by dataset. This is the contract every importer writes
 * into a species' `sourceIds` field, and what services/importwrite reads
 * back to match species across imports by ID instead of only by name (a
 * name can change — a spelling fix, a genus move — the ID it's filed
 * under usually doesn't).
 *
 * Known keys are empirically the ones actually in use across the tree
 * today (checklistbank, col, gbif, itis, wikidata, wfo, mycobank, worms —
 * see portal/public/data/sources-report.json's per-kingdom sourceIds
 * tally, via aggregateSources.ts), not a fixed enum: the index signature
 * leaves room for a dataset registered in the sources manifest but not yet
 * producing any sourceIds (ncbi, gtdb, ictv, taxref, bold) without a type
 * change first. Real data is inconsistent about a bare string vs. a
 * string array per key (col/itis/wikidata are usually arrays — a species
 * can carry more than one historical ID from the same source —
 * checklistbank is usually a bare string); both are valid for any key.
 */
interface SourceIds {
  checklistbank?: string | string[];
  col?: string | string[];
  gbif?: string | string[];
  itis?: string | string[];
  wikidata?: string | string[];
  wfo?: string | string[];
  mycobank?: string | string[];
  worms?: string | string[];
  [source: string]: string | string[] | undefined;
}

interface GbifSpecies {
  scientificName: string;
  species: string;
  genus: string;
  kingdom: string;
  rank: string;
  taxonomicStatus: string;
  [key: string]: unknown;
}

interface WikiSummary {
  title: string;
  extract?: string;
  thumbnail?: { source: string };
}

interface FamilyNode {
  id: string;
  name: string;
  rank: string;
  commonName: string;
  appSlug: string;
  speciesCount: number;
  phylumName?: string;
  className?: string;
  orderName?: string;
  notableMembers?: string[];
}

// ---------- helpers ----------

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

function findFamily(slug: string): FamilyNode | null {
  const tax = JSON.parse(readFileSync(TAXONOMY_PATH, "utf-8"));
  let phy = "", cls = "", ord = "";
  function walk(n: Record<string, unknown>): FamilyNode | null {
    if (n.rank === "PHYLUM" && n.name) phy = (n.name as string).toLowerCase();
    if (n.rank === "CLASS" && n.name) cls = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) ord = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      return { ...n as unknown as FamilyNode, phylumName: phy, className: cls, orderName: ord };
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      const r = walk(c);
      if (r) return r;
    }
    return null;
  }
  return walk(tax);
}

// ---------- importwrite client ----------

interface ImportWriteSpeciesResult {
  name: string;
  id: string;
  uuid?: string;
}

interface ImportWriteResult {
  added: ImportWriteSpeciesResult[];
  merged: ImportWriteSpeciesResult[];
  genusCreated: boolean;
}

async function postGenusToImportWrite(
  slug: string,
  phylum: string,
  cls: string,
  ord: string,
  genus: { id: string; name: string; description?: string; lineage?: string },
  species: Record<string, unknown>[],
): Promise<ImportWriteResult> {
  const res = await fetch(`${IMPORTWRITE_URL}/family/${slug}/species`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kingdom: KINGDOM,
      phylum,
      class: cls,
      order: ord,
      genus: { id: genus.id, name: genus.name, description: genus.description, lineage: genus.lineage },
      species,
    }),
  });
  if (!res.ok) throw new Error(`importwrite POST ${slug}/${genus.name} failed: ${res.status} ${await res.text()}`);
  return res.json();
}

async function flushImportWrite(slug: string): Promise<void> {
  const res = await fetch(`${IMPORTWRITE_URL}/family/${slug}/flush`, { method: "POST" });
  if (!res.ok) throw new Error(`importwrite flush ${slug} failed: ${res.status} ${await res.text()}`);
}

function getOrderPath(slug: string, cls?: string, ord?: string): string {
  // Try with class/order first
  if (cls && ord) {
    const p = resolve(root, cls, ord, slug);
    if (existsSync(p)) return p;
  }
  // Fall back: search under class directory
  const searchDir = cls ? resolve(root, cls) : root;
  const result = execSync(
    `find ${searchDir} -type d -name "${slug}" 2>/dev/null | head -1`,
    { encoding: "utf-8", timeout: 5000 },
  ).trim();
  if (result) return result;
  // New family: use canonical class/order/slug path (mkdirSync creates it later)
  if (cls && ord) return resolve(root, cls, ord, slug);
  // Last resort: repo root
  return resolve(root, slug);
}

// ---------- GBIF Cache ----------

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, { gbifKey: number; species: { species: string; genus: string; family: string }[] }>;
  familyKeyToName: Record<number, string>;
}

function tryLoadCache(className: string): GbifCache | null {
  // Map portal class names to GBIF cache file names
  const cacheName: Record<string, string> = {
    actinopterygii: "actinopterygii",
    chondrichthyes: "elasmobranchii",
  };
  const cacheKey = cacheName[className.toLowerCase()] || className.toLowerCase();
  const rawPath = resolve(portalRoot, `data/gbif-cache-${cacheKey}.json`);
  const gzPath = resolve(portalRoot, `data/gbif-cache-${cacheKey}.json.gz`);

  // Try .json.gz first (compressed for git)
  if (existsSync(gzPath)) {
    try { return JSON.parse(gunzipSync(readFileSync(gzPath)).toString("utf-8")); } catch { return null; }
  }
  // Fall back to .json
  if (existsSync(rawPath)) {
    try { return JSON.parse(readFileSync(rawPath, "utf-8")); } catch { return null; }
  }
  // Legacy name
  const legacy = resolve(portalRoot, "data/gbif-cache.json");
  if (existsSync(legacy)) {
    try { return JSON.parse(readFileSync(legacy, "utf-8")); } catch { return null; }
  }
  return null;
}

function lookupFamilyInCache(cache: GbifCache, familyName: string): { gbifKey: number; species: { species: string; genus: string }[] } | null {
  const entry = cache.speciesByFamily[familyName];
  if (!entry) return null;
  // Remove duplicates by species name
  const seen = new Set<string>();
  const unique = entry.species.filter(s => {
    if (!s.species || seen.has(s.species)) return false;
    seen.add(s.species);
    return true;
  });
  return { gbifKey: entry.gbifKey, species: unique };
}

// ---------- GBIF API ----------

async function getGbifFamilyKey(familyName: string): Promise<number> {
  // Try match API first
  const matchRes = await fetch(`${GBIF_MATCH}?name=${encodeURIComponent(familyName)}&rank=FAMILY`);
  const matchData = await matchRes.json();
  if (matchData.usageKey && matchData.matchType !== "HIGHERRANK" && matchData.usageKey > 100) {
    return matchData.usageKey;
  }

  // Fall back to search API for exact family match
  const searchRes = await fetch(`${GBIF_SEARCH}?q=${encodeURIComponent(familyName)}&rank=FAMILY&limit=5`);
  const searchData = await searchRes.json();
  const results = searchData.results || [];
  const exact = results.find((r: any) => r.canonicalName?.toLowerCase() === familyName.toLowerCase());
  if (exact?.nubKey) return exact.nubKey;
  if (exact?.key) return exact.key;

  throw new Error(`GBIF could not find family "${familyName}" (match returned key=${matchData.usageKey}, matchType=${matchData.matchType})`);
}

async function fetchGbifSpecies(familyKey: number, limit = 300): Promise<GbifSpecies[]> {
  const all: GbifSpecies[] = [];
  let offset = 0;
  const pageSize = 100;
  let total = 0;

  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED&limit=${pageSize}&offset=${offset}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.results || data.results.length === 0) break;
    total = data.count ?? 0;
    all.push(...data.results.filter((r: GbifSpecies) => r.species));
    offset += pageSize;
    if (offset >= total || offset >= limit) break;
    await sleep(300); // rate limit
  }

  return all;
}

function parseScientificName(raw: string): string {
  // Remove authority and extras: "Fulica atra Linnaeus, 1758" → "Fulica atra"
  // Also handle: "Fulica atra (Linnaeus, 1758)" 
  return raw.replace(/\([^)]*\)/g, "").replace(/,?\s*[A-Z][a-z]+.*$/, "").trim();
}

function nameToId(name: string): string {
  return name.replace(/ /g, "_").toUpperCase();
}

// ---------- Wikipedia API ----------

async function fetchWikipediaSummary(sciName: string): Promise<WikiSummary | null> {
  const encoded = encodeURIComponent(sciName);
  try {
    const res = await fetch(`${WIKI_SUMMARY}/${encoded}`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) {
      // Try the Wikipedia page title format (underscores instead of spaces)
      const altName = sciName.replace(/ /g, "_");
      const res2 = await fetch(`${WIKI_SUMMARY}/${altName}`, {
        signal: AbortSignal.timeout(10000),
      });
      if (!res2.ok) return null;
      return res2.json();
    }
    return res.json();
  } catch {
    return null;
  }
}

/** Infer continents from a text description using keyword matching */
function inferContinents(text: string): string[] {
  const found: string[] = [];
  const patterns: [RegExp, string][] = [
    [/\bEurope\b/i, "Europe"],
    [/\b(eurasian|palearctic)\b/i, "Europe"],
    [/\b(Asia|Asian|Siberia|Himalayas?)\b/i, "Asia"],
    [/\b(Africa|African|sub-Saharan|Sahara)\b/i, "Africa"],
    [/\bNorth America|North American|United States|Canada|Mexico\b/i, "North America"],
    [/\bSouth America|South American|Amazon|Andes|Brazil|Argentina\b/i, "South America"],
    [/\bAustralia|Australian|Tasmania\b/i, "Australia"],
    [/\bAntarctic(a|tic)?\b/i, "Antarctica"],
  ];

  for (const [re, continent] of patterns) {
    if (re.test(text)) {
      // Avoid duplicates
      if (!found.includes(continent)) found.push(continent);
    }
  }

  return found;
}

/** Generate a description from Wikipedia extract (first 1-3 sentences) */
function extractDescription(extract: string): string {
  // Take first 2-3 sentences
  const sentences = extract.split(/(?<=\.)\s+/).filter(s => s.length > 10);
  return sentences.slice(0, Math.min(3, sentences.length)).join(" ");
}

/** Try to extract a better common name from Wikipedia */
function getCommonName(wiki: WikiSummary, sciName: string): string {
  const title = wiki.title;
  // If the title is different from the scientific name, it's likely a common name
  if (title.toLowerCase() !== sciName.toLowerCase()) return title;
  // Fall back: use first sentence of extract
  const ex = wiki.extract || "";
  const match = ex.match(/^([A-Z][a-z]+(?:\s+[a-z]+){0,4})/);
  if (match && match[1].toLowerCase() !== sciName.toLowerCase()) return match[1];
  return sciName;
}

// ---------- main ----------

async function main() {
  const startTime = Date.now();
  const slug = process.argv[2];
  const maxSpecies = process.argv[3] ? parseInt(process.argv[3], 10) : null;

  if (!slug) {
    console.log("Usage: npx tsx scripts/fetchSpeciesFromApi.ts <appSlug> [maxSpecies]");
    console.log("  Fetches real species data from GBIF + Wikipedia");
    console.log("  maxSpecies limits how many species to fetch (default: unlimited)");
    console.log("  Set NO_WIKI=1 to skip Wikipedia enrichment (faster, less data)");
    process.exit(1);
  }

  const family = findFamily(slug);
  if (!family) {
    console.error(`❌ Family "${slug}" not found in taxonomy.json`);
    process.exit(1);
  }

  console.log(`📦 ${family.name} (${family.className}/${family.orderName}/${family.appSlug})`);
  console.log(`   speciesCount in taxonomy: ${family.speciesCount}`);

  // 1. Try local cache first
  const cacheClass = family.className || "aves";
  const cache = tryLoadCache(cacheClass);
  // gbifKey (the per-species usage key, e.g. 2436351) is only available from
  // the live API, not the cache — it's what lets importwrite match a species
  // across imports even if the name later changes (a spelling fix, a genus
  // move). Cache-sourced species fall back to name-only matching, same as
  // before.
  let allSpecies: { species: string; genus: string; gbifKey?: number }[] = [];
  let fromCache = false;

  if (cache) {
    const cached = lookupFamilyInCache(cache, family.name);
    if (cached) {
      allSpecies = cached.species;
      fromCache = true;
      console.log(`   ✅ Found ${allSpecies.length} species in local cache (${cacheClass})`);
    }
  }

  // 2. Fall back to live GBIF API
  if (!fromCache) {
    console.log("\n🔍 Looking up family in GBIF...");
    let familyKey: number;
    try {
      familyKey = await getGbifFamilyKey(family.name);
      console.log(`   GBIF taxon key: ${familyKey}`);
    } catch (e) {
      console.error(`   ❌ ${(e as Error).message}`);
      process.exit(1);
    }

    console.log("\n📡 Fetching species from GBIF...");
    try {
      const raw = await fetchGbifSpecies(familyKey, maxSpecies ?? 999999);
      allSpecies = raw.map((s: GbifSpecies) => ({
        species: s.species || s.species,
        genus: s.genus || "",
        gbifKey: typeof s.key === "number" ? s.key : undefined,
      }));
      console.log(`   Found ${allSpecies.length} accepted species`);
    } catch (e) {
      console.error(`   ❌ GBIF error: ${(e as Error).message}`);
      process.exit(1);
    }
  }

  if (allSpecies.length === 0) {
    console.log("   No species found — exit");
    process.exit(0);
  }

  // 3. Group by genus
  const genusMap = new Map<string, { species: string; genus: string; gbifKey?: number }[]>();
  for (const sp of allSpecies) {
    const sciName = sp.species || "";
    const genusName = sp.genus || sciName.split(" ")[0] || "Unknown";
    if (!sciName || !sciName.includes(" ")) continue;
    if (!genusMap.has(genusName)) genusMap.set(genusName, []);
    genusMap.get(genusName)!.push(sp);
  }

  // 4. Enrich with Wikipedia (optional)
  const useWiki = !process.env.NO_WIKI;
  let wikiCount = 0;

  if (useWiki) {
    console.log("\n📖 Enriching with Wikipedia data...");
  }

  // 5. Build the family data file
  const children: Record<string, unknown>[] = [];

  for (const [genusName, spp] of genusMap) {
    const speciesChildren: Record<string, unknown>[] = [];

    for (const sp of spp) {
      const sciName = sp.species || "";
      if (!sciName || !sciName.includes(" ")) continue;
      const speciesEpithet = sciName.split(" ").slice(1).join("_") || "sp";

      // Try Wikipedia for enrichment
      let commonName = "";
      let description = "";
      let continents: string[] = [];

      if (useWiki) {
        await sleep(RATE_LIMIT_DELAY);
        try {
          const wiki = await fetchWikipediaSummary(sciName);
          if (wiki && wiki.extract) {
            commonName = getCommonName(wiki, sciName);
            description = extractDescription(wiki.extract);
            continents = inferContinents(wiki.extract);
            wikiCount++;
          }
        } catch {
          // Wikipedia failed silently — use defaults
        }
      }

      // Don't fabricate descriptions — leave empty so enrichment can find real content
      if (!description) {
        description = "";
      }

      if (!commonName) {
        commonName = ""; // Don't fabricate common names — leave empty for enrichment to find real ones
      }

      const sourcedFrom = (useWiki && description && description.length > 40 && !description.startsWith(sciName)) ? "wikipedia" : "none";

      const node: Record<string, unknown> = {
        id: nameToId(sciName),
        name: sciName,
        rank: "SPECIES",
        commonName,
        lineage: genusName,
        continents,
        subspeciesCount: 0,
        description,
        sourcedFrom,
      };
      // Lets importwrite match this species by GBIF usage key on a later
      // import, instead of only by name — see services/importwrite/README.md.
      if (sp.gbifKey) {
        const sourceIds: SourceIds = { gbif: String(sp.gbifKey) };
        node.sourceIds = sourceIds;
      }
      speciesChildren.push(node);
    }

    // Sort species by name
    speciesChildren.sort((a, b) => (a.name as string).localeCompare(b.name as string));

    children.push({
      id: `GENUS_${genusName.toUpperCase()}`,
      name: genusName,
      rank: "GENUS",
      description: `${genusName} — a genus of ${family.commonName.toLowerCase()} in the family ${family.name}.`,
      lineage: genusName,
      children: speciesChildren,
    });
  }

  // 6. Write data file — either through importwrite (merges with whatever's
  // already there, no clobbering a concurrent import to the same family) or
  // directly, as before.
  const totalSpecies = allSpecies.length;

  if (IMPORTWRITE_URL) {
    console.log(`\n📤 Sending ${children.length} genera to importwrite at ${IMPORTWRITE_URL}...`);
    let added = 0, merged = 0, newUuids = 0;
    for (const genus of children) {
      const g = genus as { id: string; name: string; description?: string; lineage?: string; children: Record<string, unknown>[] };
      const result = await postGenusToImportWrite(slug, family.phylumName || "", family.className || "", family.orderName || "", g, g.children);
      added += result.added.length;
      merged += result.merged.length;
      // The arbiter assigns a species' permanent uuid on first add (never
      // re-derived from placement, see services/importwrite/uuid.go) and
      // returns it here so a caller logging its own import run records
      // the identity actually assigned, not one the transformer guessed.
      newUuids += result.added.filter((s) => s.uuid).length;
    }
    await flushImportWrite(slug);
    if (newUuids > 0) console.log(`   🆔 ${newUuids} new species assigned a uuid by importwrite`);
    console.log(`   ✅ importwrite: ${added} added, ${merged} merged into existing data`);
  } else {
    const familyDir = getOrderPath(slug, family.className, family.orderName);
    const dataDir = resolve(familyDir, "src/data");
    const dataFile = resolve(dataDir, `${slug}.json`);

    if (!existsSync(dataDir)) {
      mkdirSync(dataDir, { recursive: true });
    }

    const familyData = {
      id: `FAM_${family.name.toUpperCase()}`,
      name: family.name,
      rank: "FAMILY",
      commonName: family.commonName,
      children,
    };

    writeFileSync(dataFile, JSON.stringify(familyData, null, 2) + "\n");
    console.log(`\n✅ Wrote ${totalSpecies} species to ${dataFile}`);
  }

  console.log(`   ${children.length} genera, ${wikiCount} Wikipedia pages used`);

  // 7. Update speciesCount in taxonomy.json
  const currentCount = family.speciesCount;
  const newCount = Math.max(currentCount, totalSpecies);

  if (newCount !== currentCount || totalSpecies > currentCount) {
    console.log(`\n📊 Updating speciesCount: ${currentCount} → ${newCount}`);
    const taxPath = TAXONOMY_PATH;
    const tax = JSON.parse(readFileSync(taxPath, "utf-8"));

    function updateCount(n: Record<string, unknown>) {
      if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
        n.speciesCount = newCount;
        return true;
      }
      for (const c of (n.children ?? []) as Record<string, unknown>[]) {
        if (updateCount(c)) return true;
      }
      return false;
    }

    if (updateCount(tax)) {
      writeFileSync(taxPath, JSON.stringify(tax, null, 2) + "\n");
      console.log(`   Updated ${TAXONOMY_INPUT}`);
    }
  }

  // 8. Rebuild (skip during batch imports via NO_BUILD=1; kingdom-aware)
  if (process.env.NO_BUILD) {
    console.log("\n⏭  NO_BUILD set — skipping rebuild (build once after batch).");
  } else {
    console.log("\n⏳ Rebuilding unified taxonomy...");
    try {
      const kEnv = SN_KINGDOM ? `SN_KINGDOM=${SN_KINGDOM} ` : "";
      const out = execSync(`${kEnv}sh scripts/buildData.sh 2>&1`, { cwd: portalRoot, encoding: "utf-8", timeout: 180000 });
      const doneLine = out.split("\n").find(l => l.startsWith("Done"));
      if (doneLine) console.log(`   ${doneLine}`);
    } catch (e) {
      console.log(`   ⚠  Build issue: ${(e as Error).message.slice(0, 100)}`);
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
  console.log(`\n⏱  Completed in ${elapsed}s`);
  console.log(`   ${totalSpecies} species from GBIF (${wikiCount} enriched via Wikipedia)`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
