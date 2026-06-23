import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const CLASS_ARG = process.argv[2] || "Aves";
const CACHE_PATH = resolve(portalRoot, `data/gbif-cache-${CLASS_ARG.toLowerCase()}.json`);
const PAGE_SIZE = 100;
const RATE_DELAY = 250;

interface GbifSpecies {
  species: string;
  genus: string;
  family: string;
  order: string;
  class: string;
  scientificName: string;
}

interface FamilyCache {
  gbifKey: number;
  species: GbifSpecies[];
}

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, FamilyCache>;
  familyKeyToName: Record<number, string>;
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  console.log(`📡 Downloading all ${CLASS_ARG} species from GBIF...\n`);

  // 1. Get class key
  console.log(`🔍 Fetching ${CLASS_ARG} class key...`);
  const matchRes = await fetch(`${GBIF_MATCH}?name=${encodeURIComponent(CLASS_ARG)}&rank=CLASS`);
  const matchData = await matchRes.json() as { usageKey?: number; status?: string };
  const avesKey = matchData.usageKey;
  if (!avesKey) { console.error("❌ Could not find Aves in GBIF"); process.exit(1); }
  console.log(`   Class key: ${avesKey}\n`);

  // 2. Get total count
  const countRes = await fetch(`${GBIF_SEARCH}?higherTaxonKey=${avesKey}&rank=SPECIES&status=ACCEPTED&limit=1`);
  const countData = await countRes.json() as { count?: number };
  const total = countData.count ?? 0;
  console.log(`📊 ${total.toLocaleString()} bird species in GBIF`);

  // 3. Paginate all species
  const species: GbifSpecies[] = [];
  let offset = 0;
  const startTime = Date.now();

  while (offset < total) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${avesKey}&rank=SPECIES&status=ACCEPTED&limit=${PAGE_SIZE}&offset=${offset}`;
    try {
      const res = await fetch(url);
      const data = await res.json() as { results?: GbifSpecies[] };
      const batch = data.results?.filter(r => r.species && r.genus && r.family) ?? [];
      species.push(...batch);
      offset += PAGE_SIZE;
      const pct = Math.min(100, Math.round(offset / total * 100));
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
      console.log(`   ${offset.toLocaleString().padStart(6)}/${total}  (${pct}%)  ${elapsed}s  -  ${batch.length} species in this page`);
      await sleep(RATE_DELAY);
    } catch (e) {
      console.log(`   ⚠  Failed at offset ${offset}, retrying in 2s...`);
      await sleep(2000);
      offset -= PAGE_SIZE; // retry this page
    }
  }

  // 4. Group by family
  const byFamily: Record<string, FamilyCache> = {};
  const keyToName: Record<number, string> = {};
  let familyCount = 0;

  for (const sp of species) {
    if (!byFamily[sp.family]) {
      byFamily[sp.family] = { gbifKey: 0, species: [] };
      familyCount++;
    }
    byFamily[sp.family].species.push(sp);
  }

  // 5. Get GBIF family keys for each family name
  console.log(`\n🔍 Resolving ${familyCount} family keys...`);
  const familyNames = Object.keys(byFamily);
  for (let i = 0; i < familyNames.length; i++) {
    const name = familyNames[i];
    try {
      const res = await fetch(`${GBIF_MATCH}?name=${encodeURIComponent(name)}&rank=FAMILY`);
      const data = await res.json() as { usageKey?: number };
      if (data.usageKey) {
        byFamily[name].gbifKey = data.usageKey;
        keyToName[data.usageKey] = name;
      }
    } catch {
      // Skip failed lookups
    }
    if ((i + 1) % 20 === 0) console.log(`   ${i + 1}/${familyNames.length} keys resolved`);
    await sleep(100);
  }

  // 6. Write cache
  const cache: GbifCache = {
    downloadedAt: new Date().toISOString(),
    speciesByFamily: byFamily,
    familyKeyToName: keyToName,
  };

  writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2));
  const mb = (Buffer.byteLength(JSON.stringify(cache), "utf-8") / 1024 / 1024).toFixed(1);

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
  console.log(`\n✅ Done in ${elapsed}s`);
  console.log(`   ${species.length.toLocaleString()} species across ${familyCount} families`);
  console.log(`   Cache file: ${mb} MB → ${CACHE_PATH}`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
