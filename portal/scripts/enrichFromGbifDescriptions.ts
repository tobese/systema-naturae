/**
 * enrichFromGbifDescriptions.ts — fill EMPTY species descriptions from GBIF's
 * /species/{key}/descriptions endpoint. English-only + strict quality gate so no
 * voucher/distribution/checklist fragments or non-English text get in.
 *
 * Key resolution: enumerate species→usageKey per family via GBIF species search
 * (uses the family gbifKey cached in data/gbif-cache-<class>.json, ~1 call/100
 * species); falls back to per-species /species/match when no cache.
 *
 * Idempotent: only touches species with an EMPTY description. Sets
 * sourcedFrom="gbif". Resumable via /tmp/gbif-desc-cache.json.
 *
 * Usage:
 *   npx tsx scripts/enrichFromGbifDescriptions.ts --class gastropoda
 *   npx tsx scripts/enrichFromGbifDescriptions.ts --all
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const SEARCH = "https://api.gbif.org/v1/species/search";
const MATCH = "https://api.gbif.org/v1/species/match";
const SPECIES = "https://api.gbif.org/v1/species";
const UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; gbif-desc)";
const CONCURRENCY = 8;
const DELAY = 60;
const CACHE_PATH = "/tmp/gbif-desc-cache.json";

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
const binomial = (n: string) => n.split(/\s+/).slice(0, 2).join(" ");

// Persistent result cache: binomial -> description | "" (miss)
let cache: Record<string, string> = existsSync(CACHE_PATH) ? JSON.parse(readFileSync(CACHE_PATH, "utf-8")) : {};
let cacheDirty = 0;
function saveCache() { writeFileSync(CACHE_PATH, JSON.stringify(cache)); cacheDirty = 0; }

// Taxonomic-treatment / specimen-description fragments (dominant junk in GBIF
// descriptions for obscure taxa). Match keyword at start even without a colon.
const REJECT_PREFIX = /^(voucher|distribution|note|notes|habitat|type|types|material|materials|specimens?|etymology|holotype|paratype|lectotype|neotype|syntype|diagnosis|remarks?|locality|localities|range|measurements?|dimensions?|description|redescription|occurrence|comparison|comments?|discussion|morphology|coloration|colour|color|derivation)\b/i;
// Specimen-catalog codes (MB.C.31294, FMNH-P 30418, GIT 426-392) and type-description jargon.
const CATALOG = /\b[A-Z]{2,}[.\- ]?[A-Z]?[.\- ]?\d{3,}/;
const SPECIMEN_JARGON = /\b(holotype|paratype|lectotype|neotype|syntype|phragmocone|body chamber|conch|type specimen|type locality|type material|coll\.|leg\.|n\. sp\.|nov\.|sp\. nov|pl\. \d|fig\. \d|figs\. \d)\b/i;

function stripHtml(s: string): string { return s.replace(/<[^>]+>/g, " ").replace(/&[a-z]+;/gi, " ").replace(/\s+/g, " ").trim(); }

function qualityOk(text: string): boolean {
  if (!text) return false;
  // Latin script only (reject if too many non-latin letters)
  const letters = text.replace(/[^A-Za-z\u00C0-\u024F]/g, "");
  const latin = text.replace(/[^A-Za-z]/g, "");
  if (letters.length > 0 && latin.length / letters.length < 0.6) return false;
  if (REJECT_PREFIX.test(text.trim())) return false;
  if (CATALOG.test(text)) return false;          // specimen catalog numbers
  if (SPECIMEN_JARGON.test(text)) return false;  // type-description jargon
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length < 10) return false;
  if (!/[.!?]/.test(text)) return false; // must contain a sentence
  // Positive signal: reads like a species summary (has a linking verb early).
  if (!/\b(is|are|was|were|has|have|inhabits?|occurs?|lives?|feeds?|belongs?|found|native|endemic|distributed|known)\b/i.test(text)) return false;
  return true;
}

function firstSentences(text: string, n = 3): string {
  const clean = stripHtml(text);
  const s = clean.split(/(?<=[.!?])\s+/).slice(0, n).join(" ");
  return (s.length > 40 ? s : clean).slice(0, 600);
}

interface WithLang { language?: string; description?: string }
async function fetchJson(url: string): Promise<any | null> {
  for (let a = 0; a < 3; a++) {
    try {
      const res = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(20000) });
      if (res.status === 429) { await sleep(2000 * (a + 1)); continue; }
      if (!res.ok) return null;
      return await res.json();
    } catch { if (a < 2) await sleep(1500); }
  }
  return null;
}

async function descriptionForKey(key: number): Promise<string> {
  const data = await fetchJson(`${SPECIES}/${key}/descriptions`);
  const results: WithLang[] = data?.results ?? [];
  const eng = results.filter(r => (r.language === "eng" || r.language?.startsWith("en")) && r.description);
  // longest English prose that passes the gate
  let best = "";
  for (const r of eng.sort((a, b) => (b.description!.length - a.description!.length))) {
    const cleaned = stripHtml(r.description!);
    if (qualityOk(cleaned)) { best = firstSentences(cleaned); break; }
  }
  return best;
}

// Build canonicalName -> usageKey map for a family via its GBIF family key.
async function familyKeyMap(familyGbifKey: number): Promise<Map<string, number>> {
  const map = new Map<string, number>();
  let offset = 0;
  for (;;) {
    const data = await fetchJson(`${SEARCH}?highertaxonKey=${familyGbifKey}&rank=SPECIES&limit=100&offset=${offset}`);
    if (!data?.results?.length) break;
    for (const r of data.results as { key: number; canonicalName?: string }[]) {
      if (r.canonicalName) map.set(r.canonicalName, r.key);
    }
    if (data.endOfRecords) break;
    offset += 100;
    if (offset > 20000) break;
    await sleep(DELAY);
  }
  return map;
}

async function matchKey(name: string): Promise<number | null> {
  const data = await fetchJson(`${MATCH}?name=${encodeURIComponent(name)}&strict=true`);
  return data?.usageKey ?? null;
}

interface FamilyFile { path: string; slug: string; cls: string; famName: string; toEnrich: { idx: number; sci: string }[]; data: Record<string, unknown>; }

function scanFiles(classFilter?: string): FamilyFile[] {
  const families: FamilyFile[] = [];
  function processFile(fullPath: string) {
    try {
      const data = JSON.parse(readFileSync(fullPath, "utf-8"));
      const parts = fullPath.replace(root + "/", "").split("/");
      const cls = parts[0];
      const toEnrich: { idx: number; sci: string }[] = [];
      let idx = 0;
      function walk(n: Record<string, unknown>) {
        if (n.rank === "SPECIES") {
          if (!((n.description as string) || "").trim()) {
            const name = (n.name as string) || "";
            if (name && name.includes(" ")) toEnrich.push({ idx, sci: name });
          }
          idx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
      }
      walk(data);
      if (toEnrich.length > 0) families.push({ path: fullPath, slug: (data.appSlug as string) || "", cls, famName: (data.name as string) || "", toEnrich, data });
    } catch { /* skip */ }
  }
  function walkDir(dir: string) {
    let e: string[]; try { e = readdirSync(dir); } catch { return; }
    for (const x of e) {
      const full = join(dir, x);
      let st; try { st = statSync(full); } catch { continue; }
      if (st.isDirectory()) walkDir(full);
      else if (x.endsWith(".json") && full.includes("/src/data/")) processFile(full);
    }
  }
  const skip = new Set(["portal", "scripts", "docs", "node_modules", ".git", ".github", ".claude", ".opencode", ".playwright-mcp", ".vscode", "shared", "tools", "tasks"]);
  if (classFilter) walkDir(join(root, classFilter));
  else for (const e of readdirSync(root)) { if (skip.has(e) || e.startsWith(".")) continue; try { if (statSync(join(root, e)).isDirectory()) walkDir(join(root, e)); } catch { /* */ } }
  return families;
}

const classKeyMapCache = new Map<string, Record<string, number>>(); // class -> famNameLower -> gbifKey
function familyGbifKey(cls: string, famName: string): number | null {
  if (!classKeyMapCache.has(cls)) {
    const p = resolve(portalRoot, `data/gbif-cache-${cls}.json`);
    const m: Record<string, number> = {};
    if (existsSync(p)) {
      try {
        const c = JSON.parse(readFileSync(p, "utf-8"));
        for (const [fname, v] of Object.entries(c.speciesByFamily ?? {})) m[fname.toLowerCase()] = (v as { gbifKey: number }).gbifKey;
      } catch { /* */ }
    }
    classKeyMapCache.set(cls, m);
  }
  return classKeyMapCache.get(cls)![famName.toLowerCase()] ?? null;
}

async function enrichFamily(fam: FamilyFile): Promise<number> {
  // Resolve keys: prefer family enumeration, else per-species match.
  const famKey = familyGbifKey(fam.cls, fam.famName);
  const keyMap = famKey ? await familyKeyMap(famKey) : new Map<string, number>();

  // Determine which species still need a lookup (not in cache)
  const pending = fam.toEnrich.filter(t => cache[binomial(t.sci)] === undefined);
  // Resolve descriptions with concurrency
  for (let i = 0; i < pending.length; i += CONCURRENCY) {
    const batch = pending.slice(i, i + CONCURRENCY);
    await Promise.all(batch.map(async t => {
      const bin = binomial(t.sci);
      let key = keyMap.get(bin) ?? keyMap.get(t.sci) ?? null;
      if (!key) key = await matchKey(bin);
      const desc = key ? await descriptionForKey(key) : "";
      cache[bin] = desc || "";
      if (++cacheDirty >= 50) saveCache();
    }));
    await sleep(DELAY);
  }

  // Apply from cache
  let enriched = 0;
  const want = new Map(fam.toEnrich.map(t => [t.idx, binomial(t.sci)]));
  let idx = 0;
  function walk(n: Record<string, unknown>) {
    if (n.rank === "SPECIES") {
      const bin = want.get(idx);
      if (bin) {
        const d = cache[bin];
        if (d) { n.description = d; n.sourcedFrom = "gbif"; enriched++; }
      }
      idx++;
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
  }
  walk(fam.data);
  return enriched;
}

async function main() {
  let classFilter = "";
  for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--class" && i + 1 < process.argv.length) classFilter = process.argv[++i].toLowerCase();
    else if (a === "--all") classFilter = "";
    else if (!a.startsWith("--")) classFilter = a.toLowerCase();
  }

  console.log(`📖 Scanning empty species${classFilter ? ` (class=${classFilter})` : " (all)"}…`);
  const families = scanFiles(classFilter || undefined);
  const total = families.reduce((s, f) => s + f.toEnrich.length, 0);
  console.log(`   ${families.length} families · ${total} empty species to check via GBIF descriptions\n`);
  if (!families.length) { console.log("Nothing to do."); return; }

  let totalEnriched = 0;
  const start = Date.now();
  for (let i = 0; i < families.length; i++) {
    const n = await enrichFamily(families[i]);
    totalEnriched += n;
    if (n > 0) writeFileSync(families[i].path, JSON.stringify(families[i].data, null, 2) + "\n");
    if ((i + 1) % 20 === 0 || i === families.length - 1) {
      saveCache();
      const el = ((Date.now() - start) / 1000).toFixed(0);
      console.log(`   [${i + 1}/${families.length}] ${totalEnriched} enriched · ${el}s`);
    }
  }
  saveCache();
  console.log(`\n✅ Done — ${totalEnriched} species enriched from GBIF descriptions`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
