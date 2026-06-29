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

async function main() {
  const args = process.argv.slice(2);
  const familyName = args[0] || "Chrysomelidae";
  const familyKey = parseInt(args[1] || "7780", 10);

  console.log(`\n📦 Downloading all ${familyName} species from GBIF (key=${familyKey})...`);

  const allSpecies = await paginate(`${GBIF_SEARCH}?higherTaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED`);
  console.log(`   Downloaded ${allSpecies.length} species records`);

  const species: SpeciesRecord[] = allSpecies.map(s => ({
    scientificName: s.scientificName || s.canonicalName || "",
    canonicalName: s.canonicalName || "",
    genus: s.genus || (s.canonicalName || "").split(" ")[0] || "",
    species: s.species || s.canonicalName || "",
    order: (s.order || s.higherClassificationMap?.order || "").replace(/\s+/g, ""),
    family: (s.family || s.higherClassificationMap?.family || "").replace(/\s+/g, ""),
  }));

  const cache = {
    downloadedAt: new Date().toISOString(),
    speciesByFamily: {
      [familyName]: {
        gbifKey: familyKey,
        species,
      },
    },
  };

  const slug = familyName.toLowerCase();
  const outPath = resolve(root, "portal", "data", `gbif-cache-${slug}.json`);
  writeFileSync(outPath, JSON.stringify(cache, null, 2) + "\n");
  console.log(`\n✅ ${species.length} species for ${familyName}`);
  console.log(`   → Saved to portal/data/gbif-cache-${slug}.json`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
