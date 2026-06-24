import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";
const RATE_DELAY = 120; // ms between Wikipedia calls
const CONCURRENCY = 3; // parallel Wikipedia requests

interface ApiResult {
  title: string;
  extract?: string;
  thumbnail?: { source: string };
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

// Reuse the continent inference and description extraction from fetchSpeciesFromApi
const CONTINENT_PATTERNS: [RegExp, string][] = [
  [/\bEurope\b/i, "Europe"], [/\b(eurasian|palearctic)\b/i, "Europe"],
  [/\b(Asia|Asian|Siberia|Himalayas?)\b/i, "Asia"],
  [/\b(Africa|African|sub-Saharan|Sahara)\b/i, "Africa"],
  [/\bNorth America|North American|United States|Canada|Mexico\b/i, "North America"],
  [/\bSouth America|South American|Amazon|Andes|Brazil|Argentina\b/i, "South America"],
  [/\bAustralia|Australian|Tasmania\b/i, "Australia"],
  [/\bAntarctic(a|tic)?\b/i, "Antarctica"],
];

function inferContinents(text: string): string[] {
  const found: string[] = [];
  for (const [re, continent] of CONTINENT_PATTERNS) {
    if (re.test(text) && !found.includes(continent)) found.push(continent);
  }
  return found;
}

function extractDescription(extract: string): string {
  const sentences = extract.split(/(?<=\.)\s+/).filter(s => s.length > 10);
  return sentences.slice(0, Math.min(3, sentences.length)).join(" ");
}

async function fetchWiki(sciName: string): Promise<{ commonName: string; description: string; continents: string[] } | null> {
  const encoded = encodeURIComponent(sciName.replace(/ /g, "_"));
  try {
    const res = await fetch(`${WIKI_SUMMARY}/${encoded}`, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) return null;
    const data = await res.json() as ApiResult;
    if (!data.extract) return null;
    return {
      commonName: data.title !== sciName ? data.title : sciName,
      description: extractDescription(data.extract),
      continents: inferContinents(data.extract),
    };
  } catch {
    return null;
  }
}

interface FamilyFile {
  path: string;
  slug: string;
  speciesCount: number;
  toEnrich: { idx: number; sciName: string }[];
  data: Record<string, unknown>;
}

function scanFiles(classFilter?: string): FamilyFile[] {
  const families: FamilyFile[] = [];

  function processFile(fullPath: string) {
    const slug = fullPath.match(/\/([^/]+)\.json$/)?.[1] || "";
    if (!slug) return;

    try {
      const data = JSON.parse(readFileSync(fullPath, "utf-8"));
      const toEnrich: { idx: number; sciName: string }[] = [];
      let idx = 0;

      function walk(n: Record<string, unknown>) {
        if (n.rank === "SPECIES") {
          const src = n.sourcedFrom as string || "";
          if (src !== "wikipedia") {
            const name = n.name as string || "";
            if (name && name.includes(" ")) toEnrich.push({ idx, sciName: name });
          }
          idx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
      }
      walk(data);

      if (toEnrich.length > 0) {
        families.push({ path: fullPath, slug, speciesCount: idx, toEnrich, data });
      }
    } catch {
      // skip unparseable files
    }
  }

  // Walk the aves/ directory tree recursively
  function walkDir(dir: string) {
    try {
      for (const entry of readdirSync(dir)) {
        const full = join(dir, entry);
        if (statSync(full).isDirectory()) {
          walkDir(full);
        } else if (entry.endsWith(".json") && full.includes("/src/data/")) {
          processFile(full);
        }
      }
    } catch { /* permission denied, skip */ }
  }

  // Walk class directories — also catch tardigrada (phylum at root) and any others
  const classDirs = classFilter
    ? [classFilter]
    : ["aves", "mammalia", "reptilia", "chondrichthyes", "amphibia", "actinopterygii",
      "insecta", "arachnida", "asteroidea", "echinoidea", "holothuroidea", "tardigrada"];
  for (const dir of classDirs) {
    const fullDir = join(root, dir);
    if (existsSync(fullDir)) walkDir(fullDir);
  }
  return families;
}

async function enrichFamily(fam: FamilyFile): Promise<number> {
  let enriched = 0;
  const total = fam.toEnrich.length;

  // Process in batches with concurrency
  for (let batchStart = 0; batchStart < total; batchStart += CONCURRENCY) {
    const batch = fam.toEnrich.slice(batchStart, batchStart + CONCURRENCY);

    const results = await Promise.all(
      batch.map(item => fetchWiki(item.sciName).then(wiki => ({ item, wiki })))
    );

    for (const { item, wiki } of results) {
      if (!wiki) continue;

      // Find and update the species node at this idx
      let currentIdx = 0;
      function updateNode(n: Record<string, unknown>): boolean {
        if (n.rank === "SPECIES") {
          if (currentIdx === item.idx) {
            n.sourcedFrom = "wikipedia";
            n.description = wiki.description;
            n.commonName = wiki.commonName;
            n.continents = wiki.continents.length > 0 ? wiki.continents : n.continents;
            return true;
          }
          currentIdx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) {
          if (updateNode(c)) return true;
        }
        return false;
      }
      if (updateNode(fam.data)) enriched++;
    }

    // Set sourcedFrom=generated for species where Wikipedia had nothing
    let nonWikiIdx = 0;
    function tagGenerated(n: Record<string, unknown>) {
      if (n.rank === "SPECIES") {
        if (n.sourcedFrom !== "wikipedia") n.sourcedFrom = "generated";
        nonWikiIdx++;
      }
      for (const c of (n.children ?? []) as Record<string, unknown>[]) tagGenerated(c);
    }
    // Only tag at end of each batch if we're past the last window
    if (batchStart + CONCURRENCY >= total) {
      tagGenerated(fam.data);
    }

    if (batchStart % (CONCURRENCY * 5) === 0 && batchStart > 0) {
      const pct = Math.round(batchStart / total * 100);
      console.log(`   ${batchStart}/${total} done (${pct}%)`);
    }
  }

  return enriched;
}

async function main() {
  // Parse arguments: optionally --class <classname> or <slug>
  let classFilter = "";
  let slugFilter = "";
  for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i] === "--class" && i + 1 < process.argv.length) {
      classFilter = process.argv[++i].toLowerCase();
    } else if (!slugFilter) {
      slugFilter = process.argv[i];
    }
  }

  console.log("📖 Scanning family data files...");
  const all = scanFiles(classFilter || undefined);
  const families = slugFilter
    ? all.filter(f => f.slug === slugFilter)
    : all;

  console.log(`   Found ${families.length} families with ${families.reduce((s, f) => s + f.toEnrich.length, 0)} species to enrich`);

  if (families.length === 0) {
    console.log("   Nothing to do.");
    process.exit(0);
  }

  let totalEnriched = 0;
  const startTime = Date.now();

  for (let i = 0; i < families.length; i++) {
    const fam = families[i];
    const pct = Math.round((i + 1) / families.length * 100);
    console.log(`\n[${i + 1}/${families.length}] (${pct}%) ${fam.slug} — ${fam.toEnrich.length} species to check`);

    const enriched = await enrichFamily(fam);
    totalEnriched += enriched;

    if (enriched > 0) {
      writeFileSync(fam.path, JSON.stringify(fam.data, null, 2) + "\n");
    }

    console.log(`   → ${enriched} enriched, ${fam.toEnrich.length - enriched} already OK`);

    // Progress summary every 20 families
    if ((i + 1) % 20 === 0 || i === families.length - 1) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
      console.log(`\n📊 ${i + 1}/${families.length} families · ${totalEnriched} species enriched · ${elapsed}s elapsed`);
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
  console.log(`\n✅ Done in ${elapsed}s`);
  console.log(`   ${families.length} families processed, ${totalEnriched} species enriched`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
