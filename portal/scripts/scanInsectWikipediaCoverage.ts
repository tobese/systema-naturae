import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const WIKI_API = "https://en.wikipedia.org/w/api.php";

const RATE_DELAY = 150;
const WIKI_BATCH_SIZE = 50;
const WIKI_DELAY = 100;
const MAX_RETRIES = 3;
const SAMPLE_SIZE = 5000;

interface FamilyTarget {
  slug: string;
  name: string;
  target: number;
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

async function fetchWithRetry(url: string, retries = MAX_RETRIES): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
      if (res.ok) return res;
      if (res.status === 429) {
        console.log(`   ⚠️ Rate limited, waiting ${(i + 1) * 2}s...`);
        await sleep((i + 1) * 2000);
      }
    } catch (e) {
      if (i < retries) {
        console.log(`   ⚠️ Retry ${i + 1}/${retries}...`);
        await sleep((i + 1) * 1000);
      }
    }
  }
  throw new Error(`Failed after ${retries} retries: ${url}`);
}

async function getFamilyKey(familyName: string): Promise<number | null> {
  try {
    const res = await fetchWithRetry(`${GBIF_MATCH}?name=${encodeURIComponent(familyName)}&rank=FAMILY`);
    const data = await res.json() as { usageKey?: number };
    return data.usageKey ?? null;
  } catch {
    return null;
  }
}

async function fetchFamilySpecies(familyKey: number, familyName: string): Promise<string[]> {
  const all: string[] = [];
  let offset = 0;
  const pageSize = 100;
  let total = 0;
  let retries = 0;

  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED&limit=${pageSize}&offset=${offset}`;
    try {
      const res = await fetchWithRetry(url);
      const data = await res.json() as { results?: { species?: string }[]; count?: number };
      if (!data.results || data.results.length === 0) break;
      total = data.count ?? 0;
      const names = data.results
        .map(r => r.species)
        .filter((s): s is string => !!s && s.includes(" "));
      all.push(...names);
      offset += pageSize;
      retries = 0;
      if (offset >= total) break;
      await sleep(RATE_DELAY);
    } catch {
      retries++;
      if (retries > 3) break;
      await sleep(2000);
    }
  }

  return all;
}

async function checkWikipediaExistence(names: string[]): Promise<Set<string>> {
  const found = new Set<string>();

  for (let i = 0; i < names.length; i += WIKI_BATCH_SIZE) {
    const batch = names.slice(i, i + WIKI_BATCH_SIZE);
    const encoded = batch.map(t => encodeURIComponent(t.replace(/ /g, "_"))).join("|");
    const url = `${WIKI_API}?action=query&titles=${encoded}&format=json&origin=*`;

    let success = false;
    for (let retry = 0; retry <= MAX_RETRIES; retry++) {
      try {
        const res = await fetchWithRetry(url);
        const data = await res.json() as {
          query?: {
            normalized?: { from: string; to: string }[];
            pages?: Record<string, { missing?: string; title?: string }>;
          };
        };

        const normalized = new Map<string, string>();
        for (const n of data.query?.normalized ?? []) {
          normalized.set(n.to, n.from);
        }

        for (const [pageId, page] of Object.entries(data.query?.pages ?? {})) {
          if (pageId === "-1" || page.missing) {
            // Missing
          } else {
            const existingTitle = page.title ?? "";
            if (existingTitle) {
              const original = normalized.get(existingTitle) ?? existingTitle.replace(/_/g, " ");
              found.add(original);
            }
          }
        }
        success = true;
        break;
      } catch {
        if (retry < MAX_RETRIES) {
          console.log(`   ⚠️ Wiki batch failed, retry ${retry + 1}/${MAX_RETRIES}...`);
          await sleep((retry + 1) * 1000);
        }
      }
    }

    if (!success) {
      console.log(`   ❌ Failed to check batch ${i}-${i + WIKI_BATCH_SIZE}, skipping`);
    }

    if ((i / WIKI_BATCH_SIZE + 1) % 10 === 0) {
      console.log(`   ${Math.min(i + WIKI_BATCH_SIZE, names.length)}/${names.length} checked (${found.size} found)`);
    }

    await sleep(WIKI_DELAY);
  }

  return found;
}

async function scanFamily(fam: FamilyTarget): Promise<{ target: number; gbifCount: number; wikiCount: number; coveragePct: number } | null> {
  console.log(`\n[${fam.slug}] ${fam.name} — target: ${fam.target.toLocaleString()}`);

  const familyKey = await getFamilyKey(fam.name);
  if (!familyKey) {
    console.log(`   ❌ Could not find GBIF family key`);
    return null;
  }

  const species = await fetchFamilySpecies(familyKey, fam.name);
  console.log(`   📡 GBIF: ${species.length.toLocaleString()} accepted species`);

  if (species.length === 0) {
    return { target: fam.target, gbifCount: 0, wikiCount: 0, coveragePct: 0 };
  }

  const sample = species.length > SAMPLE_SIZE
    ? species.sort(() => Math.random() - 0.5).slice(0, SAMPLE_SIZE)
    : species;

  console.log(`   🔍 Checking Wikipedia for ${sample.length.toLocaleString()} species...`);
  const wikiFound = await checkWikipediaExistence(sample);
  const wikiCount = wikiFound.size;
  const coveragePct = sample.length > 0 ? (wikiCount / sample.length) * 100 : 0;

  const extrapolatedWiki = species.length > sample.length
    ? Math.round(wikiCount / sample.length * species.length)
    : wikiCount;

  console.log(`   ✅ Wikipedia: ${wikiCount}/${sample.length} (${coveragePct.toFixed(1)}%) — extrapolated: ~${extrapolatedWiki.toLocaleString()}`);

  return {
    target: fam.target,
    gbifCount: species.length,
    wikiCount: extrapolatedWiki,
    coveragePct: parseFloat(coveragePct.toFixed(1)),
  };
}

async function main() {
  const taxonomy = JSON.parse(readFileSync(resolve(portalRoot, "data/taxonomy.json"), "utf-8"));

  const insectFamilies: FamilyTarget[] = [];
  function walk(node: any) {
    if (node.rank === "CLASS" && node.name === "Insecta") {
      for (const order of node.children ?? []) {
        for (const family of order.children ?? []) {
          if (family.rank === "FAMILY" && family.appSlug && family.speciesCount) {
            insectFamilies.push({
              slug: family.appSlug,
              name: family.name,
              target: family.speciesCount,
            });
          }
        }
      }
    }
    for (const child of node.children ?? []) walk(child);
  }
  walk(taxonomy);

  console.log(`📊 Scanning ${insectFamilies.length} insect families for Wikipedia coverage\n`);

  const results: Record<string, { target: number; gbifCount: number; wikiCount: number; coveragePct: number }> = {};

  for (const fam of insectFamilies) {
    const result = await scanFamily(fam);
    if (result) {
      results[fam.slug] = result;
    }
  }

  // Write report
  const reportPath = resolve(portalRoot, "data/insect-wikipedia-coverage.json");
  writeFileSync(reportPath, JSON.stringify(results, null, 2) + "\n");

  // Print summary
  console.log("\n" + "=".repeat(80));
  console.log("INSECT WIKIPEDIA COVERAGE REPORT");
  console.log("=".repeat(80));
  console.log(`${"Family".padEnd(20)} ${"Target".padEnd(8)} ${"GBIF".padEnd(8)} ${"Wiki~".padEnd(8)} ${"Coverage".padEnd(10)} ${"Action"}`);
  console.log("-".repeat(80));

  for (const [slug, r] of Object.entries(results)) {
    const action = r.coveragePct > 15 ? "⭐ Wikipedia-first import"
      : r.coveragePct > 5 ? "📝 Mixed import"
      : r.coveragePct > 0 ? "⚠️ Low coverage — full synthetic"
      : "❌ No Wikipedia data";
    console.log(`${slug.padEnd(20)} ${String(r.target).padEnd(8)} ${String(r.gbifCount).padEnd(8)} ${String(r.wikiCount).padEnd(8)} ${(r.coveragePct + "%").padEnd(10)} ${action}`);
  }

  console.log("=".repeat(80));
  console.log(`Report saved: ${reportPath}`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
