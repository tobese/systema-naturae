/**
 * enrichFromWikipediaDB.ts — enrich species descriptions from the LOCAL offline
 * Wikipedia SQLite dump (no network, no rate limit).
 *
 * Mirrors enrichFromWikipedia.ts (same file-walk, idempotency, node update) but
 * sources descriptions from /Volumes/WikiDump/wiki-pages.sqlite via the sqlite3
 * CLI (bulk `title IN (...)` queries). Idempotent: skips species already
 * sourcedFrom="wikipedia"; only fills species with no real description.
 *
 * Usage:
 *   npx tsx scripts/enrichFromWikipediaDB.ts            # all class dirs, all kingdoms
 *   npx tsx scripts/enrichFromWikipediaDB.ts --class gastropoda
 *   npx tsx scripts/enrichFromWikipediaDB.ts --all      # explicit all
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");

const DB = process.env.WIKI_DB || "/Volumes/WikiDump/wiki-pages.sqlite";
const CHUNK = 500;

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
  const clean = extract.replace(/\n+/g, " ").trim();
  const sentences = clean.split(/(?<=\.)\s+/).filter(s => s.length > 10);
  const out = sentences.slice(0, Math.min(3, sentences.length)).join(" ");
  return out.length > 30 ? out : (clean.length > 30 ? clean : "");
}

const binomial = (n: string) => n.split(/\s+/).slice(0, 2).join(" ");

/** Bulk lookup binomials in the SQLite DB. Returns Map<binomial, extract>. */
function bulkLookup(names: string[]): Map<string, string> {
  const map = new Map<string, string>();
  const bins = [...new Set(names.map(binomial).filter(Boolean))];
  for (let i = 0; i < bins.length; i += CHUNK) {
    const chunk = bins.slice(i, i + CHUNK);
    const inList = chunk.map(b => `'${b.replace(/'/g, "''")}'`).join(",");
    const sql = `SELECT title, extract FROM pages WHERE title IN (${inList}) AND extract IS NOT NULL;`;
    const r = spawnSync("sqlite3", ["-json", DB, sql], { encoding: "utf-8", timeout: 60000, maxBuffer: 200 * 1024 * 1024 });
    if (r.status !== 0 || !r.stdout) continue;
    try {
      const rows = JSON.parse(r.stdout) as { title: string; extract: string }[];
      for (const row of rows) {
        if (!map.has(row.title)) map.set(row.title, row.extract);
      }
    } catch { /* ignore parse errors */ }
  }
  return map;
}

interface FamilyFile { path: string; slug: string; total: number; toEnrich: { idx: number; sciName: string }[]; data: Record<string, unknown>; }

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
          // Only fill species with NO real description. This preserves all
          // existing real content (wikipedia, powo, websearch, nzpcn, …) and
          // only enriches empty/stripped species.
          const desc = ((n.description as string) || "").trim();
          if (!desc) {
            const name = (n.name as string) || "";
            if (name && name.includes(" ")) toEnrich.push({ idx, sciName: name });
          }
          idx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
      }
      walk(data);
      if (toEnrich.length > 0) families.push({ path: fullPath, slug, total: idx, toEnrich, data });
    } catch { /* skip */ }
  }

  function walkDir(dir: string) {
    let entries: string[];
    try { entries = readdirSync(dir); } catch { return; }
    for (const entry of entries) {
      const full = join(dir, entry);
      let st;
      try { st = statSync(full); } catch { continue; }
      if (st.isDirectory()) walkDir(full);
      else if (entry.endsWith(".json") && full.includes("/src/data/")) processFile(full);
    }
  }

  const skip = new Set(["portal", "scripts", "docs", "node_modules", ".git", ".github", ".claude", ".opencode", ".playwright-mcp", ".vscode", "shared", "tools", "tasks"]);
  if (classFilter) {
    walkDir(join(root, classFilter));
  } else {
    for (const e of readdirSync(root)) {
      if (skip.has(e) || e.startsWith(".")) continue;
      let st; try { st = statSync(join(root, e)); } catch { continue; }
      if (st.isDirectory()) walkDir(join(root, e));
    }
  }
  return families;
}

function enrichFamily(fam: FamilyFile): number {
  const lookup = bulkLookup(fam.toEnrich.map(t => t.sciName));
  if (lookup.size === 0) return 0;

  let enriched = 0;
  const wantByIdx = new Map(fam.toEnrich.map(t => [t.idx, t.sciName]));
  let idx = 0;
  function walk(n: Record<string, unknown>): void {
    if (n.rank === "SPECIES") {
      const sci = wantByIdx.get(idx);
      if (sci) {
        const extract = lookup.get(binomial(sci));
        if (extract) {
          const desc = extractDescription(extract);
          if (desc) {
            n.sourcedFrom = "wikipedia";
            n.description = desc;
            const cont = inferContinents(extract);
            if (cont.length > 0) n.continents = cont;
            enriched++;
          }
        }
      }
      idx++;
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
  }
  walk(fam.data);
  return enriched;
}

function main() {
  let classFilter = "";
  for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--class" && i + 1 < process.argv.length) classFilter = process.argv[++i].toLowerCase();
    else if (a === "--all") classFilter = "";
    else if (!a.startsWith("--")) classFilter = a.toLowerCase();
  }

  if (!existsSync(DB)) { console.error(`❌ SQLite DB not found: ${DB}`); process.exit(1); }

  console.log(`📖 Scanning family files${classFilter ? ` (class=${classFilter})` : " (all kingdoms)"}…`);
  const families = scanFiles(classFilter || undefined);
  const totalToCheck = families.reduce((s, f) => s + f.toEnrich.length, 0);
  console.log(`   ${families.length} families · ${totalToCheck} species to check against local DB\n`);
  if (families.length === 0) { console.log("Nothing to do."); return; }

  let totalEnriched = 0;
  const start = Date.now();
  for (let i = 0; i < families.length; i++) {
    const fam = families[i];
    const n = enrichFamily(fam);
    totalEnriched += n;
    if (n > 0) writeFileSync(fam.path, JSON.stringify(fam.data, null, 2) + "\n");
    if ((i + 1) % 50 === 0 || i === families.length - 1) {
      const el = ((Date.now() - start) / 1000).toFixed(0);
      console.log(`   [${i + 1}/${families.length}] ${totalEnriched} enriched · ${el}s`);
    }
  }
  const el = ((Date.now() - start) / 1000).toFixed(0);
  console.log(`\n✅ Done in ${el}s — ${totalEnriched} species enriched from local DB`);
}

main();
