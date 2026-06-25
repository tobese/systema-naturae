import { writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";

const RATE_DELAY = 200;
const WIKI_DELAY = 150;

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

interface Species {
  name: string;
  genus: string;
  commonName?: string;
  description?: string;
  continents?: string[];
  sourcedFrom?: string;
}

async function fetchWithRetry(url: string, retries = 3): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
      if (res.ok) return res;
      if (res.status === 429) await sleep((i + 1) * 3000);
    } catch {
      if (i < retries) await sleep((i + 1) * 1000);
    }
  }
  throw new Error(`Failed: ${url}`);
}

async function getFamilyKey(familyName: string): Promise<number | null> {
  const res = await fetchWithRetry(`${GBIF_MATCH}?name=${encodeURIComponent(familyName)}&rank=FAMILY`);
  const data = await res.json() as { usageKey?: number };
  return data.usageKey ?? null;
}

async function fetchSpecies(familyKey: number): Promise<Species[]> {
  const all: Species[] = [];
  let offset = 0;
  const pageSize = 100;

  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED&limit=${pageSize}&offset=${offset}`;
    const res = await fetchWithRetry(url);
    const data = await res.json() as { results?: { species?: string; genus?: string }[]; count?: number };
    if (!data.results || data.results.length === 0) break;

    for (const r of data.results) {
      if (r.species && r.genus) {
        all.push({ name: r.species, genus: r.genus });
      }
    }

    offset += pageSize;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_DELAY);
  }

  return all;
}

async function checkAndEnrichWikipedia(species: Species): Promise<Species | null> {
  const encoded = encodeURIComponent(species.name.replace(/ /g, "_"));
  try {
    const res = await fetchWithRetry(`${WIKI_SUMMARY}/${encoded}`);
    if (!res.ok) return null;
    
    const data = await res.json() as { 
      title?: string; 
      extract?: string; 
      thumbnail?: { source: string };
      type?: string;
    };
    
    // Skip disambiguation pages and other non-articles
    if (data.type === "disambiguation") return null;
    if (!data.extract || data.extract.length < 20) return null;

    // Infer continents from extract
    const continents: string[] = [];
    const patterns: [RegExp, string][] = [
      [/\bEurope\b/i, "Europe"], [/\bAsia\b/i, "Asia"], [/\bAfrica\b/i, "Africa"],
      [/\bNorth America\b/i, "North America"], [/\bSouth America\b/i, "South America"],
      [/\bAustralia\b/i, "Australia"], [/\bAntarctica\b/i, "Antarctica"],
    ];
    for (const [re, cont] of patterns) {
      if (re.test(data.extract) && !continents.includes(cont)) continents.push(cont);
    }

    // Extract description (first 1-3 sentences)
    const sentences = data.extract.split(/(?<=\.)\s+/).filter(s => s.length > 10);
    const description = sentences.slice(0, Math.min(3, sentences.length)).join(" ");

    return {
      ...species,
      commonName: data.title !== species.name ? data.title : undefined,
      description,
      continents,
      sourcedFrom: "wikipedia",
    };
  } catch {
    return null;
  }
}

async function main() {
  console.log("🦋 Fetching Papilionidae (swallowtail butterflies) from GBIF...\n");

  const familyKey = await getFamilyKey("Papilionidae");
  if (!familyKey) {
    console.error("❌ Could not find GBIF family key");
    process.exit(1);
  }

  // 1. Fetch all species
  console.log("📡 Fetching species from GBIF...");
  const species = await fetchSpecies(familyKey);
  console.log(`   Found ${species.length} accepted species\n`);

  // 2. Check Wikipedia and enrich in one pass
  console.log("🔍 Checking Wikipedia and enriching...");
  const enriched: Species[] = [];
  for (let i = 0; i < species.length; i++) {
    const s = species[i];
    const result = await checkAndEnrichWikipedia(s);
    if (result) {
      enriched.push(result);
    }
    if ((i + 1) % 50 === 0 || i === species.length - 1) {
      console.log(`   ${i + 1}/${species.length} checked (${enriched.length} Wikipedia articles)`);
    }
    await sleep(WIKI_DELAY);
  }
  console.log(`   ✅ ${enriched.length} species with real Wikipedia articles\n`);

  if (enriched.length === 0) {
    console.log("❌ No Wikipedia articles found");
    process.exit(1);
  }

  // 3. Build tree structure (group by genus)
  const genusMap = new Map<string, Species[]>();
  for (const s of enriched) {
    if (!genusMap.has(s.genus)) genusMap.set(s.genus, []);
    genusMap.get(s.genus)!.push(s);
  }

  const children = Array.from(genusMap.entries()).map(([genus, speciesList]) => ({
    id: `GEN_${genus.toUpperCase().replace(/[^A-Z]/g, "_")}`,
    name: genus,
    rank: "GENUS",
    children: speciesList.map((s, i) => ({
      id: `SP_${s.name.toUpperCase().replace(/[^A-Z]/g, "_")}_${i}`,
      name: s.name,
      rank: "SPECIES",
      commonName: s.commonName,
      description: s.description,
      continents: s.continents,
      subspeciesCount: 0,
      sourcedFrom: s.sourcedFrom,
    })),
  }));

  const tree = {
    id: "FAM_PAPILIONIDAE",
    name: "Papilionidae",
    rank: "FAMILY",
    commonName: "Swallowtail butterflies",
    children,
  };

  // 4. Write
  const outPath = resolve(portalRoot, "../insecta/lepidoptera/papilionidae/src/data/papilionidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2) + "\n");

  console.log(`✅ Wrote ${enriched.length} Wikipedia-backed species to:`);
  console.log(`   ${outPath}`);
  console.log(`   ${children.length} genera`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
