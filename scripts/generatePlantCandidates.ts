/**
 * Generate plant species candidate list via Wikidata SPARQL.
 *
 * Queries by GBIF family names (batches of 20). Saves incrementally
 * so partial progress is not lost on timeout.
 *
 * Usage:
 *   npx tsx scripts/generatePlantCandidates.ts
 *   npx tsx scripts/generatePlantCandidates.ts --resume  # skip cached families
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const WDQS_URL = "https://query.wikidata.org/sparql";
const USER_AGENT = "systema-naturae/0.1 (plant-candidates; tb@anomaly.co)";
const BATCH_SIZE = 20;
const BATCH_SPACING_MS = 2000;
const MAX_RETRIES = 5;

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

const CACHE_PATH = resolve(root, "shared", "data", "plant-candidates.json");
const NAMES_PATH = resolve(root, "shared", "data", "plant-species-names.json");

function getAllLandPlantFamilies(): string[] {
  const phyla = ["tracheophyta", "bryophyta", "marchantiophyta", "anthocerotophyta"];
  const families = new Set<string>();
  for (const p of phyla) {
    const path = resolve(root, "portal", "data", `gbif-scout-${p}.json`);
    const data = JSON.parse(readFileSync(path, "utf-8"));
    for (const cls of data.children || []) {
      for (const order of cls.children || []) {
        for (const fam of order.children || []) {
          families.add(fam.name);
        }
      }
    }
  }
  return [...families].sort();
}

function buildFamilyQuery(familyNames: string[]): string {
  const values = familyNames.map(f => `"${f.replace(/"/g, '\\"')}"`).join(" ");
  return `
SELECT ?familyName ?item ?itemLabel ?name WHERE {
  VALUES ?familyName { ${values} }
  ?family wdt:P225 ?familyName .
  ?family wdt:P105 wd:Q35409 .
  ?item wdt:P171* ?family .
  ?item wdt:P105 wd:Q7432 .
  ?item wdt:P225 ?name .
  ?article schema:about ?item .
  ?article schema:isPartOf <https://en.wikipedia.org/> .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}`;
}

async function runQuery(sparql: string): Promise<any[]> {
  let lastErr: unknown;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(WDQS_URL, {
        method: "POST",
        headers: {
          Accept: "application/sparql-results+json",
          "Content-Type": "application/x-www-form-urlencoded",
          "User-Agent": USER_AGENT,
        },
        body: `query=${encodeURIComponent(sparql)}`,
        signal: AbortSignal.timeout(180_000),
      });
      if (!res.ok) {
        const ra = parseInt(res.headers.get("retry-after") || "0", 10);
        const wait = (ra > 0 ? ra : 2 ** attempt) * 1000;
        await sleep(wait);
        lastErr = new Error(`HTTP ${res.status}`);
        continue;
      }
      const json = (await res.json()) as { results: { bindings: any[] } };
      return json.results.bindings;
    } catch (e) {
      lastErr = e;
      await sleep(2 ** attempt * 1000);
    }
  }
  throw lastErr ?? new Error("query failed");
}

async function main() {
  const args = process.argv.slice(2);
  const resume = args.includes("--resume");

  console.log("🌿 Generating plant Wikipedia candidates via Wikidata\n");

  const allFamilies = getAllLandPlantFamilies();
  console.log(`   Total GBIF land-plant families: ${allFamilies.length}\n`);

  // Load existing progress if resuming
  let processedFamilies = new Set<string>();
  let allResults = new Map<string, string>();

  if (resume && existsSync(CACHE_PATH)) {
    const existing = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));
    if (existing._processedFamilies) {
      processedFamilies = new Set(existing._processedFamilies);
    }
    if (existing.candidates && existing._names) {
      for (let i = 0; i < existing.candidates.length; i++) {
        allResults.set(existing.candidates[i], existing._names[i] || "");
      }
    }
    console.log(`   Resuming: ${processedFamilies.size} families already done, ${allResults.size} candidates\n`);
  }

  const todoFamilies = allFamilies.filter(f => !processedFamilies.has(f));
  console.log(`   Remaining: ${todoFamilies.length} families\n`);

  const failedFamilies: string[] = [];

  for (let i = 0; i < todoFamilies.length; i += BATCH_SIZE) {
    const batch = todoFamilies.slice(i, i + BATCH_SIZE);
    const query = buildFamilyQuery(batch);

    try {
      const rows = await runQuery(query);
      for (const r of rows) {
        const title = r.itemLabel?.value || r.name?.value || "";
        const name = r.name?.value || "";
        if (title) allResults.set(title, name);
      }
      for (const f of batch) processedFamilies.add(f);

      const done = processedFamilies.size;
      const famStr = batch.length <= 3
        ? batch.join(", ")
        : `${batch[0]}…${batch[batch.length - 1]}`;
      console.log(`  [${done}/${allFamilies.length}] ${famStr} → ${rows.length} spp (total: ${allResults.size})`);

      // Save incrementally
      const candidates = [...allResults.keys()].sort();
      const names = candidates.map(c => allResults.get(c) || "");
      const out = {
        candidates,
        _names: names,
        _processedFamilies: [...processedFamilies].sort(),
        total: candidates.length,
        generatedAt: new Date().toISOString(),
      };
      writeFileSync(CACHE_PATH, JSON.stringify(out, null, 2) + "\n");

    } catch (err) {
      failedFamilies.push(...batch);
      console.error(`  ✗ [${processedFamilies.size + 1}] family batch failed:`, (err as Error).message.slice(0, 80));
    }

    await sleep(BATCH_SPACING_MS);
  }

  // Summary
  console.log(`\n📊 Summary:`);
  console.log(`   Processed families: ${processedFamilies.size}/${allFamilies.length}`);
  console.log(`   Failed families: ${failedFamilies.length}`);
  console.log(`   Total plant Wikipedia candidates: ${allResults.size}`);

  if (failedFamilies.length > 0) {
    console.log(`\n   Failed: ${failedFamilies.slice(0, 20).join(", ")}${failedFamilies.length > 20 ? "..." : ""}`);
  }

  // Final save (clean, without internal fields)
  const candidates = [...allResults.keys()].sort();
  writeFileSync(CACHE_PATH, JSON.stringify({ candidates, total: candidates.length, generatedAt: new Date().toISOString() }, null, 2) + "\n");
  console.log(`\n   Saved to ${CACHE_PATH}`);

  writeFileSync(NAMES_PATH, JSON.stringify({ species: candidates.length, skipped: 0, candidates }, null, 2) + "\n");
  console.log(`   Saved to ${NAMES_PATH}`);
}

main();
