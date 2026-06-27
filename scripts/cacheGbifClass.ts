import { writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const RATE_MS = 150;

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

async function paginate(url: string): Promise<any[]> {
  const results: any[] = [];
  let offset = 0;
  const limit = 300;
  while (true) {
    const sep = url.includes("?") ? "&" : "?";
    const res = await fetch(`${url}${sep}limit=${limit}&offset=${offset}`);
    const data = await res.json();
    if (!data.results?.length) break;
    for (const r of data.results) results.push(r);
    offset += limit;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_MS);
  }
  return results;
}

async function downloadClass(classKey: number, className: string): Promise<GbifCache> {
  console.log(`\n📦 Downloading all ${className} species from GBIF (key=${classKey})...`);

  // Get all families for this class
  const families: FamilyInfo[] = [];
  let offset = 0;
  const limit = 200;
  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${classKey}&rank=FAMILY&status=ACCEPTED&limit=${limit}&offset=${offset}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.results?.length) break;
    for (const r of data.results) {
      if (r.canonicalName) families.push({ name: r.canonicalName, gbifKey: r.nubKey || r.key, speciesCount: r.speciesCount ?? 0 });
    }
    offset += limit;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_MS);
  }
  console.log(`   Found ${families.length} families`);

  // Get ALL species for the class in one paginated pass
  console.log(`   Downloading species (classKey=${classKey})...`);
  const allSpecies = await paginate(`${GBIF_SEARCH}?higherTaxonKey=${classKey}&rank=SPECIES&status=ACCEPTED`);
  console.log(`   Downloaded ${allSpecies.length} species records`);

  // Group by family
  const familyMap = new Map<string, SpeciesRecord[]>();
  for (const s of allSpecies) {
    const fam = (s.family || s.higherClassificationMap?.family || "").replace(/\s+/g, "");
    if (!fam) continue;
    if (!familyMap.has(fam)) familyMap.set(fam, []);
    familyMap.get(fam)!.push({
      scientificName: s.scientificName || s.canonicalName || "",
      canonicalName: s.canonicalName || "",
      genus: s.genus || (s.canonicalName || "").split(" ")[0] || "",
      species: s.species || s.canonicalName || "",
      order: (s.order || s.higherClassificationMap?.order || "").replace(/\s+/g, ""),
      family: fam,
    });
  }

  // Build result — use species count from each family as gbifKey estimate
  const speciesByFamily: Record<string, { gbifKey: number; species: SpeciesRecord[] }> = {};
  let totalSpecies = 0;
  for (const [famName, spp] of familyMap) {
    const famInfo = families.find(f => f.name.toLowerCase() === famName.toLowerCase());
    speciesByFamily[famName] = { gbifKey: famInfo?.gbifKey ?? 0, species: spp };
    totalSpecies += spp.length;
  }

  console.log(`\n✅ ${totalSpecies} species across ${Object.keys(speciesByFamily).length} families`);

  // Add empty entries for families with no species found (keep them for taxonomy completeness)
  for (const fam of families) {
    if (!speciesByFamily[fam.name]) {
      speciesByFamily[fam.name] = { gbifKey: fam.gbifKey, species: [] };
    }
  }

  return {
    downloadedAt: new Date().toISOString(),
    speciesByFamily,
  };
}

async function main() {
  const args = process.argv.slice(2);
  const className = args[0] || "Anthozoa";
  const classKey = parseInt(args[1] || "206", 10);

  const cache = await downloadClass(classKey, className);
  const outPath = resolve(root, "portal", "data", `gbif-cache-${className.toLowerCase()}.json`);
  writeFileSync(outPath, JSON.stringify(cache, null, 2) + "\n");
  console.log(`\n   → Saved to portal/data/gbif-cache-${className.toLowerCase()}.json`);
}

main();
