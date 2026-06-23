import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const CLASS_ARG = process.argv[2] || "Aves";

// Map portal class names → GBIF class names (GBIF doesn't use all the same names)
const CLASS_NAME_MAP: Record<string, string> = {
  actinopterygii: "Actinopterygii",  // GBIF key: 100198473 (fallback)
  chondrichthyes: "Elasmobranchii",
  // Echinoderm classes work as-is
};

// Pre-set class keys for classes GBIF's match API can't find
const CLASS_KEY_OVERRIDE: Record<string, number> = {
  actinopterygii: parseInt(process.env.GBIF_FISH_KEY || "177709486", 10),
};
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

  // 1. Get class key (check for fixed overrides and name mappings)
  const gbifClassName = CLASS_NAME_MAP[CLASS_ARG.toLowerCase()] || CLASS_ARG;
  let classKey = CLASS_KEY_OVERRIDE[CLASS_ARG.toLowerCase()];

  if (!classKey) {
    console.log(`🔍 Fetching ${gbifClassName} class key from GBIF...`);
    try {
      const matchRes = await fetch(`${GBIF_MATCH}?name=${encodeURIComponent(gbifClassName)}&rank=CLASS`);
      const matchData = await matchRes.json() as { usageKey?: number; status?: string };
      classKey = matchData.usageKey;
    } catch {
      // Fall through to error below
    }
  }

  if (!classKey) {
    console.error(`❌ Could not find a GBIF class key for "${CLASS_ARG}" (tried "${gbifClassName}")`);
    console.error(`   To provide a key manually: GBIF_CLASS_KEY=12345 npx tsx scripts/cacheGbifData.ts ${CLASS_ARG}`);
    process.exit(1);
  }
  console.log(`   Class: ${gbifClassName}, key: ${classKey}\n`);

  // 2. Get total count
  const countRes = await fetch(`${GBIF_SEARCH}?higherTaxonKey=${classKey}&rank=SPECIES&status=ACCEPTED&limit=1`);
  const countData = await countRes.json() as { count?: number };
  const total = countData.count ?? 0;
  console.log(`📊 ${total.toLocaleString()} bird species in GBIF`);

  // 3. Paginate all species
  const species: GbifSpecies[] = [];
  let offset = 0;
  const startTime = Date.now();

  let retries = 0;
  while (offset < total) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${classKey}&rank=SPECIES&status=ACCEPTED&limit=${PAGE_SIZE}&offset=${offset}`;
    let batch: GbifSpecies[] = [];
    try {
      retries = 0;
      const res = await fetch(url);
      const data = await res.json() as { results?: GbifSpecies[]; count?: number };

      // GBIF sometimes returns empty results past the real end of data
      if (!data.results || data.results.length === 0) {
        // If count is 0 but we're past the real data, the offset may be past the true end
        console.log(`   ∅ Empty page at offset ${offset} — stopping (found ${species.length} total)`);
        break;
      }

      batch = data.results.filter(r => r.species && r.genus && r.family);

      species.push(...batch);
      offset += PAGE_SIZE;
      const pct = Math.round(species.length / total * 100);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
      console.log(`   ${species.length.toLocaleString().padStart(6)}/${total}  (${pct}%)  ${elapsed}s`);
      await sleep(RATE_DELAY);
    } catch {
      retries++;
      if (retries > 5) {
        console.log(`   ❌ Failed ${retries} times at offset ${offset} — stopping`);
        break;
      }
      console.log(`   ⚠  Retry ${retries}/5 at offset ${offset}...`);
      await sleep(3000);
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
