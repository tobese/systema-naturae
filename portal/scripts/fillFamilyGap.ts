import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";
import { gunzipSync } from "zlib";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";
const RATE_LIMIT_DELAY = 150;

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, { gbifKey: number; species: { species: string; genus: string; family: string }[] }>;
  familyKeyToName: Record<number, string>;
}

interface WikiSummary {
  title: string;
  extract?: string;
  thumbnail?: { source: string };
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

function tryLoadCache(className: string): GbifCache | null {
  const cacheName: Record<string, string> = {
    actinopterygii: "actinopterygii",
    chondrichthyes: "elasmobranchii",
  };
  const cacheKey = cacheName[className.toLowerCase()] || className.toLowerCase();
  const rawPath = resolve(portalRoot, `data/gbif-cache-${cacheKey}.json`);
  const gzPath = resolve(portalRoot, `data/gbif-cache-${cacheKey}.json.gz`);

  if (existsSync(gzPath)) {
    try { return JSON.parse(gunzipSync(readFileSync(gzPath)).toString("utf-8")); } catch { return null; }
  }
  if (existsSync(rawPath)) {
    try { return JSON.parse(readFileSync(rawPath, "utf-8")); } catch { return null; }
  }
  return null;
}

function lookupFamilyInCache(cache: GbifCache, familyName: string): { species: { species: string; genus: string }[] } | null {
  const entry = cache.speciesByFamily[familyName];
  if (!entry) return null;
  const seen = new Set<string>();
  const unique = entry.species.filter(s => {
    if (!s.species || seen.has(s.species)) return false;
    seen.add(s.species);
    return true;
  });
  return { species: unique };
}

async function fetchWikipediaSummary(sciName: string): Promise<WikiSummary | null> {
  const encoded = encodeURIComponent(sciName);
  try {
    const res = await fetch(`${WIKI_SUMMARY}/${encoded}`, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) {
      const altName = sciName.replace(/ /g, "_");
      const res2 = await fetch(`${WIKI_SUMMARY}/${altName}`, { signal: AbortSignal.timeout(10000) });
      if (!res2.ok) return null;
      return res2.json();
    }
    return res.json();
  } catch {
    return null;
  }
}

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
    if (re.test(text) && !found.includes(continent)) found.push(continent);
  }
  return found;
}

function extractDescription(extract: string): string {
  const sentences = extract.split(/(?<=\.)\s+/).filter(s => s.length > 10);
  return sentences.slice(0, Math.min(3, sentences.length)).join(" ");
}

function nameToId(name: string): string {
  return name.replace(/ /g, "_").toUpperCase();
}

function collectSpecies(node: Record<string, unknown>): Map<string, { genus: string; node: Record<string, unknown> }> {
  const map = new Map<string, { genus: string; node: Record<string, unknown> }>();
  for (const child of (node.children ?? []) as Record<string, unknown>[]) {
    if (child.rank === "SPECIES") {
      map.set(child.name as string, { genus: (child as any).lineage || "", node: child });
    }
    if ((child.children as Record<string, unknown>[])?.length) {
      const sub = collectSpecies(child);
      sub.forEach((v, k) => map.set(k, v));
    }
  }
  return map;
}

function findTaxonomyFamily(slug: string): Record<string, unknown> | null {
  const tax = JSON.parse(readFileSync(resolve(portalRoot, "data/taxonomy.json"), "utf-8"));
  let cls = "", ord = "";
  function walk(n: Record<string, unknown>): Record<string, unknown> | null {
    if (n.rank === "CLASS") cls = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) ord = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      return { ...n, className: cls, orderName: ord };
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      const r = walk(c);
      if (r) return r;
    }
    return null;
  }
  return walk(tax);
}

async function main() {
  const slug = process.argv[2];
  if (!slug) {
    console.log("Usage: npx tsx scripts/fillFamilyGap.ts <appSlug> [maxNew]");
    console.log("  Reads existing family data, finds missing species from GBIF cache,");
    console.log("  enriches them from Wikipedia, and appends them.");
    process.exit(1);
  }

  const maxNew = process.argv[3] ? parseInt(process.argv[3], 10) : null;
  const noWiki = !!process.env.NO_WIKI;

  // 1. Load taxonomy info
  const fam = findTaxonomyFamily(slug);
  if (!fam) { console.error(`Family "${slug}" not found in taxonomy.json`); process.exit(1); }

  const className = (fam.className as string)?.toLowerCase() || "";
  const orderName = (fam.orderName as string) || "";
  const familyName = fam.name as string;
  const targetCount = fam.speciesCount as number;

  console.log(`📦 ${familyName} (${className}/${orderName}/${slug})`);
  console.log(`   Target species: ${targetCount}`);

  // 2. Load existing data
  const dataPath = resolve(root, className, orderName, slug, "src/data", `${slug}.json`);
  if (!existsSync(dataPath)) { console.error(`Data file not found: ${dataPath}`); process.exit(1); }

  const data = JSON.parse(readFileSync(dataPath, "utf-8")) as Record<string, unknown>;
  const existing = collectSpecies(data);
  console.log(`   Existing species: ${existing.size}`);

  if (existing.size >= targetCount) {
    console.log(`   ✅ Already at or above target — nothing to do`);
    return;
  }

  // 3. Load GBIF cache
  const cache = tryLoadCache(className);
  if (!cache) { console.error(`No GBIF cache for class "${className}"`); process.exit(1); }

  const cached = lookupFamilyInCache(cache, familyName);
  if (!cached) { console.error(`Family "${familyName}" not found in GBIF cache`); process.exit(1); }

  console.log(`   GBIF cache: ${cached.species.length} species`);

  // 4. Find missing species
  const missing: { species: string; genus: string }[] = [];
  for (const sp of cached.species) {
    if (!sp.species || !sp.species.includes(" ")) continue;
    if (!existing.has(sp.species)) {
      missing.push(sp);
    }
  }

  const cap = maxNew ?? missing.length;
  const toAdd = missing.slice(0, Math.min(cap, targetCount - existing.size));
  console.log(`   Missing: ${missing.length}, will add: ${toAdd.length}`);

  if (toAdd.length === 0) {
    console.log("   Nothing to add — exit");
    return;
  }

  // 5. Group by genus
  const genusMap = new Map<string, { species: string; genus: string }[]>();
  for (const sp of toAdd) {
    const gn = sp.genus || sp.species.split(" ")[0] || "Unknown";
    if (!genusMap.has(gn)) genusMap.set(gn, []);
    genusMap.get(gn)!.push(sp);
  }

  // 6. Build index of existing genus nodes
  const genusNodes = new Map<string, Record<string, unknown>>();
  for (const child of (data.children ?? []) as Record<string, unknown>[]) {
    if (child.rank === "GENUS") {
      genusNodes.set(child.name as string, child);
    }
  }

  // 7. Enrich missing species from Wikipedia and add to data
  let wikiCount = 0;
  let newGenusCount = 0;
  let addedCount = 0;

  for (const [genusName, spp] of genusMap) {
    const speciesChildren: Record<string, unknown>[] = [];

    for (const sp of spp) {
      const sciName = sp.species;
      let description = "";
      let commonName = "";
      let continents: string[] = [];

      if (!noWiki) {
        await sleep(RATE_LIMIT_DELAY);
        try {
          const wiki = await fetchWikipediaSummary(sciName);
          if (wiki && wiki.extract) {
            description = extractDescription(wiki.extract);
            commonName = wiki.title !== sciName ? wiki.title : "";
            continents = inferContinents(wiki.extract);
            wikiCount++;
          }
        } catch { /* skip */ }
      }

      if (!description) {
        description = `${sciName} — a species in the genus ${genusName}, family ${familyName}.`;
      }
      if (!commonName) {
        const epithet = sciName.split(" ").slice(1).join(" ");
        commonName = `${genusName} ${epithet}`;
      }

      const sourcedFrom = (!noWiki && description.length > 40) ? "wikipedia" : "generated";

      speciesChildren.push({
        id: nameToId(sciName),
        name: sciName,
        rank: "SPECIES",
        commonName,
        lineage: genusName,
        continents,
        subspeciesCount: 0,
        description,
        sourcedFrom,
      });
    }

    speciesChildren.sort((a, b) => (a.name as string).localeCompare(b.name as string));

    const existingGenus = genusNodes.get(genusName);
    if (existingGenus) {
      const existingKids = (existingGenus.children ?? []) as Record<string, unknown>[];
      existingKids.push(...speciesChildren);
      existingKids.sort((a, b) => (a.name as string).localeCompare(b.name as string));
      addedCount += speciesChildren.length;
      if (process.env.VERBOSE) {
        console.log(`   Added ${speciesChildren.length} to existing genus ${genusName}`);
      }
    } else {
      (data.children as Record<string, unknown>[]).push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of ${(fam.commonName as string)?.toLowerCase() || "species"} in the family ${familyName}.`,
        lineage: genusName,
        children: speciesChildren,
      });
      newGenusCount++;
      addedCount += speciesChildren.length;
      if (process.env.VERBOSE) {
        console.log(`   Created new genus ${genusName} with ${speciesChildren.length} species`);
      }
    }
  }

  // 8. Sort genera by name
  (data.children as Record<string, unknown>[]).sort((a, b) =>
    (a.name as string).localeCompare(b.name as string)
  );

  // 9. Save
  mkdirSync(dirname(dataPath), { recursive: true });
  writeFileSync(dataPath, JSON.stringify(data, null, 2) + "\n");

  // 10. Update speciesCount in taxonomy.json
  const newTotal = existing.size + addedCount;
  const updatedCount = Math.max(targetCount, newTotal);
  const taxPath = resolve(portalRoot, "data/taxonomy.json");
  const tax = JSON.parse(readFileSync(taxPath, "utf-8"));

  function updateCount(n: Record<string, unknown>) {
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      n.speciesCount = updatedCount;
      return true;
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      if (updateCount(c)) return true;
    }
    return false;
  }

  if (updateCount(tax)) {
    writeFileSync(taxPath, JSON.stringify(tax, null, 2) + "\n");
    console.log(`   Updated taxonomy.json speciesCount: ${targetCount} → ${updatedCount}`);
  }

  console.log(`\n✅ Added ${addedCount} species (${wikiCount} Wikipedia-enriched, ${newGenusCount} new genera)`);

  // 11. Rebuild
  console.log("\n⏳ Rebuilding...");
  try {
    const out = execSync("sh scripts/buildData.sh 2>&1", { cwd: portalRoot, encoding: "utf-8", timeout: 180000 });
    const doneLine = out.split("\n").find(l => l.startsWith("Done"));
    if (doneLine) console.log(`   ${doneLine}`);
  } catch (e) {
    console.log(`   ⚠  Build: ${(e as Error).message.slice(0, 100)}`);
  }
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
