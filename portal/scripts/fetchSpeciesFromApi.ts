import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";

const RATE_LIMIT_DELAY = 150; // ms between Wikipedia calls

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
  className?: string;
  orderName?: string;
  notableMembers?: string[];
}

// ---------- helpers ----------

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

function findFamily(slug: string): FamilyNode | null {
  const tax = JSON.parse(readFileSync(resolve(portalRoot, "data/taxonomy.json"), "utf-8"));
  let cls = "", ord = "";
  function walk(n: Record<string, unknown>): FamilyNode | null {
    if (n.rank === "CLASS") cls = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) ord = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      return { ...n as unknown as FamilyNode, className: cls, orderName: ord };
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      const r = walk(c);
      if (r) return r;
    }
    return null;
  }
  return walk(tax);
}

function getOrderPath(slug: string, cls?: string, ord?: string): string {
  // Find the actual directory path
  const result = execSync(
    `find ${root}/aves -type d -name "${slug}" 2>/dev/null | head -1`,
    { encoding: "utf-8", timeout: 5000 },
  ).trim();
  if (result) return result;
  // Try with class/order
  if (cls && ord) {
    const p = resolve(root, cls, ord, slug);
    if (existsSync(p)) return p;
  }
  return resolve(root, slug);
}

// ---------- GBIF Cache ----------

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, { gbifKey: number; species: { species: string; genus: string; family: string }[] }>;
  familyKeyToName: Record<number, string>;
}

function tryLoadCache(className: string): GbifCache | null {
  const path = resolve(portalRoot, `data/gbif-cache-${className.toLowerCase()}.json`);
  if (!existsSync(path)) {
    // Try legacy name
    const legacy = resolve(portalRoot, "data/gbif-cache.json");
    if (!existsSync(legacy)) return null;
    try { return JSON.parse(readFileSync(legacy, "utf-8")); } catch { return null; }
  }
  try { return JSON.parse(readFileSync(path, "utf-8")); } catch { return null; }
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
  const url = `${GBIF_MATCH}?name=${encodeURIComponent(familyName)}&rank=FAMILY`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.usageKey) throw new Error(`GBIF could not find family "${familyName}"`);
  return data.usageKey;
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
  let allSpecies: { species: string; genus: string }[] = [];
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
      allSpecies = raw.map((s: GbifSpecies) => ({ species: s.species || s.species, genus: s.genus || "" }));
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
  const genusMap = new Map<string, { species: string; genus: string }[]>();
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

      if (!description) {
        description = `${sciName} — a species in the genus ${genusName}, family ${family.name}. ${family.commonName ? `Also known as ${family.commonName.toLowerCase()}.` : ""}`;
      }

      if (!commonName) {
        commonName = `${genusName} ${speciesEpithet}`.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
      }

      speciesChildren.push({
        id: nameToId(sciName),
        name: sciName,
        rank: "SPECIES",
        commonName,
        lineage: genusName,
        continents,
        subspeciesCount: 0,
        description,
      });
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

  // 6. Write data file
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

  const totalSpecies = allSpecies.length;
  console.log(`\n✅ Wrote ${totalSpecies} species to ${dataFile}`);
  console.log(`   ${children.length} genera, ${wikiCount} Wikipedia pages used`);

  // 7. Update speciesCount in taxonomy.json
  const currentCount = family.speciesCount;
  const newCount = Math.max(currentCount, totalSpecies);

  if (newCount !== currentCount || totalSpecies > currentCount) {
    console.log(`\n📊 Updating speciesCount: ${currentCount} → ${newCount}`);
    const taxPath = resolve(portalRoot, "data/taxonomy.json");
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
      console.log(`   Updated taxonomy.json`);
    }
  }

  // 8. Rebuild
  console.log("\n⏳ Rebuilding unified taxonomy...");
  try {
    const out = execSync("sh scripts/buildData.sh 2>&1", { cwd: portalRoot, encoding: "utf-8", timeout: 60000 });
    const doneLine = out.split("\n").find(l => l.startsWith("Done"));
    if (doneLine) console.log(`   ${doneLine}`);
  } catch (e) {
    console.log(`   ⚠  Build issue: ${(e as Error).message.slice(0, 100)}`);
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
  console.log(`\n⏱  Completed in ${elapsed}s`);
  console.log(`   ${totalSpecies} species from GBIF (${wikiCount} enriched via Wikipedia)`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
