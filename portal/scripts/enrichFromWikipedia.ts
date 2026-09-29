import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";
import { classDirsForKingdom, dirName } from "./lib/familyPath.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
// Empty SN_KINGDOM means animalia, matching the build.
const KINGDOM = process.env.SN_KINGDOM || "animalia";
const portalRoot = resolve(__dirname, "..");

const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";
const RATE_DELAY = 500; // ms between Wikipedia calls
const CONCURRENCY = 2; // parallel Wikipedia requests
const HEADERS = { "User-Agent": "systema-naturae/1.0 (enrichment; https://github.com/tb-Dev/systema-naturae)" };

interface ApiResult {
  title: string;
  type?: string;          // "standard" | "disambiguation" | "redirect" | ...
  description?: string;   // Wikipedia's one-line gloss, e.g. "Hosner's cat"
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

/** Compare names the way Wikipedia does: underscores for spaces, case-blind. */
function sameTitle(a: string, b: string): boolean {
  const norm = (s: string) => s.replace(/_/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
  return norm(a) === norm(b);
}

async function fetchWiki(sciName: string): Promise<{ commonName?: string; description: string; continents: string[] } | null> {
  const encoded = encodeURIComponent(sciName.replace(/ /g, "_"));
  const url = `${WIKI_SUMMARY}/${encoded}`;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(15000), headers: HEADERS });
      if (res.status === 429) {
        const waitMs = Math.min(Math.max(3000 * (attempt + 1), 5000), 15000);
        await sleep(waitMs);
        continue;
      }
      if (!res.ok) return null;
      const data = await res.json() as ApiResult;
      if (!data.extract) return null;

      // The summary endpoint follows redirects, so a binomial with no article of
      // its own comes back 200 with the *genus* article: asking for
      // "Dermechinus horridus" returns title "Dermechinus". The old code took
      // that extract as the species' description and the genus title as its
      // commonName, which put 327 genus-level descriptions on species nodes
      // across 15 phyla. Only a standard article whose title is the name we
      // actually asked for is evidence about that name.
      if (data.type && data.type !== "standard") return null;
      if (!sameTitle(data.title, sciName)) return null;

      // The common name comes from Wikipedia's gloss field, not from the title:
      // the title is the binomial, and writing it into commonName produced
      // entries like "Leopardus Guttulus". A gloss that just echoes the title
      // back is not a common name either.
      const gloss = (data.description ?? "").replace(/\s*\([^)]*\)\s*$/, "").trim();
      const commonName = gloss && !sameTitle(gloss, data.title) && !sameTitle(gloss, sciName)
        ? gloss
        : undefined;

      return {
        ...(commonName ? { commonName } : {}),
        description: extractDescription(data.extract),
        continents: inferContinents(data.extract),
      };
    } catch {
      if (attempt < 2) { await sleep(3000); continue; }
      return null;
    }
  }
  return null;
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

  // Walk taxonomy/<kingdom>/ rather than a hard-coded list of class
  // directories. The list was 12 names under an existsSync guard, and a guard
  // like that fails in the worst direction: the directory is not there, the
  // script skips it, and it reports success having enriched nothing. After the
  // tree moved under taxonomy/<kingdom>/<phylum>/<class>/ all 12 were gone, so
  // this had become a no-op that still exited 0.
  //
  // --class is still honoured, but resolved through the taxonomy rather than
  // assumed to be a top-level directory, so it keeps working for a class that
  // is not a direct child of the kingdom root (acoela lives under
  // xenacoelomorpha, for instance).
  const kingdomRoot = join(root, "taxonomy", KINGDOM);
  if (classFilter) {
    const dirs = classDirsForKingdom(root, KINGDOM)
      .filter((c) => c === dirName(classFilter));
    if (!dirs.length) {
      console.error(`--class ${classFilter} is not a class in ${KINGDOM}. ` +
        `Known: ${classDirsForKingdom(root, KINGDOM).join(", ")}`);
      process.exit(1);
    }
    for (const dir of dirs) {
      for (const phylum of safeReadDir(kingdomRoot)) {
        const p1 = join(kingdomRoot, phylum, dir);
        if (existsSync(p1)) walkDir(p1);
        const p2 = join(kingdomRoot, dir);
        if (existsSync(p2)) walkDir(p2);
      }
    }
  } else if (existsSync(kingdomRoot)) {
    walkDir(kingdomRoot);
  } else {
    console.error(`No taxonomy/${KINGDOM} directory. Nothing to enrich - refusing to ` +
      `report success having done nothing.`);
    process.exit(1);
  }
  if (families.length === 0) {
    console.error(`No family data files found under taxonomy/${KINGDOM}. ` +
      `Refusing to report success having enriched nothing.`);
    process.exit(1);
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

      // Find and update the species node at this idx. An arrow, not a
      // declaration: a hoisted `function` is treated as callable before the
      // `if (!wiki) continue` above, so the narrowing never reached its body
      // and every `wiki.` read was a type error.
      let currentIdx = 0;
      const updateNode = (n: Record<string, unknown>): boolean => {
        if (n.rank === "SPECIES") {
          if (currentIdx === item.idx) {
            n.sourcedFrom = "wikipedia";
            n.description = wiki.description;
            // Only overwrite when Wikipedia actually offered a gloss. The old
            // code always assigned, so a name it could not improve was
            // replaced by the binomial in title case.
            if (wiki.commonName) n.commonName = wiki.commonName;
            n.continents = wiki.continents.length > 0 ? wiki.continents : n.continents;
            return true;
          }
          currentIdx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) {
          if (updateNode(c)) return true;
        }
        return false;
      };
      if (updateNode(fam.data)) enriched++;
    }

    // Tag sourcedFrom for species where Wikipedia had nothing (don't fabricate descriptions)
    let nonWikiIdx = 0;
    function tagNonWiki(n: Record<string, unknown>) {
      if (n.rank === "SPECIES") {
        if (n.sourcedFrom !== "wikipedia") n.sourcedFrom = "none";
        nonWikiIdx++;
      }
      for (const c of (n.children ?? []) as Record<string, unknown>[]) tagNonWiki(c);
    }
    // Only tag at end of each batch if we're past the last window
    if (batchStart + CONCURRENCY >= total) {
      tagNonWiki(fam.data);
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

function safeReadDir(dir: string): string[] {
  try {
    return readdirSync(dir);
  } catch {
    return [];
  }
}
