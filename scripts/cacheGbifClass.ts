import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const RATE_MS = 300;
const MAX_RETRIES = 5;

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

interface SpeciesRecord {
  scientificName: string;
  canonicalName: string;
  genus: string;
  species: string;
  order: string;
  family: string;
}

interface FamilyInfo {
  name: string;
  gbifKey: number;
  speciesCount: number;
}

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, { gbifKey: number; species: SpeciesRecord[] }>;
}

async function fetchWithRetry(url: string, retries = MAX_RETRIES): Promise<any> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeout);
      if (!res.ok) {
        if (attempt < retries) {
          const wait = Math.min(1000 * Math.pow(2, attempt), 15000);
          console.warn(`  HTTP ${res.status}, retry ${attempt}/${retries} in ${wait}ms`);
          await sleep(wait);
          continue;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      return await res.json();
    } catch (e: any) {
      if (attempt < retries) {
        const wait = Math.min(1000 * Math.pow(2, attempt), 15000);
        console.warn(`  ${e.message || e.cause?.message || e}, retry ${attempt}/${retries} in ${wait}ms`);
        await sleep(wait);
        continue;
      }
      throw e;
    }
  }
}

async function paginate(url: string): Promise<any[]> {
  const results: any[] = [];
  let offset = 0;
  const limit = 300;
  while (true) {
    const sep = url.includes("?") ? "&" : "?";
    const data = await fetchWithRetry(`${url}${sep}limit=${limit}&offset=${offset}`);
    if (!data.results?.length) break;
    for (const r of data.results) results.push(r);
    offset += limit;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_MS);
  }
  return results;
}

async function downloadClass(classKey: number, className: string, resumePath?: string): Promise<GbifCache> {
  console.log(`\n📦 Downloading all ${className} species from GBIF (key=${classKey})...`);

  // Resume from existing cache if requested
  let speciesByFamily: Record<string, { gbifKey: number; species: SpeciesRecord[] }> = {};
  let startIndex = 0;

  if (resumePath && existsSync(resumePath)) {
    try {
      const existing = JSON.parse(readFileSync(resumePath, "utf-8")) as GbifCache;
      speciesByFamily = existing.speciesByFamily;
      startIndex = Object.keys(speciesByFamily).length;
      console.log(`   Resuming from existing cache: ${startIndex} families already done`);
    } catch (e) {
      console.log(`   Could not load existing cache, starting fresh`);
    }
  }

  // Get all families for this class
  const families: FamilyInfo[] = [];
  let offset = 0;
  const limit = 200;
  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${classKey}&rank=FAMILY&status=ACCEPTED&limit=${limit}&offset=${offset}`;
    const data = await fetchWithRetry(url);
    if (!data.results?.length) break;
    for (const r of data.results) {
      if (r.canonicalName) families.push({ name: r.canonicalName, gbifKey: r.nubKey || r.key, speciesCount: r.speciesCount ?? 0 });
    }
    offset += limit;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_MS);
  }
  console.log(`   Found ${families.length} families total, ${families.length - startIndex} remaining`);

  // Download species per-family to avoid GBIF's 100k offset limit
  console.log(`   Downloading species by family...`);
  let totalSpecies = Object.values(speciesByFamily).reduce((s, e) => s + e.species.length, 0);

  for (let i = startIndex; i < families.length; i++) {
    const fam = families[i];

    // Skip if already cached
    if (speciesByFamily[fam.name]) continue;

    try {
      const spp = await paginate(`${GBIF_SEARCH}?higherTaxonKey=${fam.gbifKey}&rank=SPECIES&status=ACCEPTED`);
      speciesByFamily[fam.name] = { gbifKey: fam.gbifKey, species: spp.map(s => ({
        scientificName: s.scientificName || s.canonicalName || "",
        canonicalName: s.canonicalName || "",
        genus: s.genus || (s.canonicalName || "").split(" ")[0] || "",
        species: s.species || s.canonicalName || "",
        order: (s.order || s.higherClassificationMap?.order || "").replace(/\s+/g, ""),
        family: fam.name,
      })) };
      totalSpecies += spp.length;

      // Save checkpoint every 10 families
      if ((i + 1) % 10 === 0 || i === families.length - 1) {
        if (resumePath) {
          const partial: GbifCache = {
            downloadedAt: new Date().toISOString(),
            speciesByFamily,
          };
          writeFileSync(resumePath, JSON.stringify(partial, null, 2) + "\n");
        }
        console.log(`   ${i + 1}/${families.length} families done (${totalSpecies} species so far)`);
      }
    } catch (e: any) {
      console.error(`   FAILED on family ${fam.name} (key ${fam.gbifKey}) after all retries: ${e.message}`);
      console.error(`   Saving checkpoint and aborting. Resume by re-running with --resume`);
      if (resumePath) {
        const partial: GbifCache = {
          downloadedAt: new Date().toISOString(),
          speciesByFamily,
        };
        writeFileSync(resumePath, JSON.stringify(partial, null, 2) + "\n");
      }
      throw e;
    }
  }

  console.log(`\n✅ ${totalSpecies} species across ${Object.keys(speciesByFamily).length} families`);

  return {
    downloadedAt: new Date().toISOString(),
    speciesByFamily,
  };
}

async function main() {
  const args = process.argv.slice(2);
  const className = args[0] || "Anthozoa";
  const classKey = parseInt(args[1] || "206", 10);
  const useResume = args.includes("--resume");

  const outPath = resolve(root, "portal", "data", `gbif-cache-${className.toLowerCase()}.json`);

  const cache = await downloadClass(classKey, className, useResume ? outPath : undefined);
  writeFileSync(outPath, JSON.stringify(cache, null, 2) + "\n");
  console.log(`\n   → Saved to portal/data/gbif-cache-${className.toLowerCase()}.json`);
}

main();
