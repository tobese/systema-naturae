/**
 * enrichFromAlgaeBase.ts — key-gated enrichment from AlgaeBase (algaebase.org),
 * the authoritative global algae database. Relevant to Chromista (diatoms, brown/
 * golden algae) and the algae held in Plantae (red/green algae).
 *
 * DORMANT until an API key is provided:
 *   export ALGAEBASE_KEY=<your key>     (request one at algaebase.org)
 *
 * Mirrors the other enrichers: walks EMPTY species only (idempotent), quality-gates
 * text, sets sourcedFrom="algaebase". Conservative rate limiting (the API is
 * key-gated and NOT for bulk harvesting — be a good citizen). Resumable cache.
 *
 * NOTE ON RESPONSE SHAPE: AlgaeBase's public API is primarily nomenclatural. The
 * exact prose/text field names are only verifiable against a live keyed response,
 * so extraction below tries several likely fields and quality-gates the result.
 * Tune FIELD_CANDIDATES once a real response is seen.
 *
 * Usage:
 *   ALGAEBASE_KEY=xxx npx tsx scripts/enrichFromAlgaeBase.ts --class bacillariophyceae
 *   ALGAEBASE_KEY=xxx npx tsx scripts/enrichFromAlgaeBase.ts --kingdom chromista
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const KEY = process.env.ALGAEBASE_KEY || "";
const API = "https://api.algaebase.org/v1.3/species";
const DELAY = 500;          // be gentle — key-gated, non-bulk API
const CONCURRENCY = 2;
const CACHE_PATH = "/tmp/algaebase-cache.json";

// Text fields to try, in priority order (tune against a live keyed response).
const FIELD_CANDIDATES = ["dcterms:description", "description", "notes", "dwc:habitat", "habitat", "morphology"];

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
const binomial = (n: string) => n.split(/\s+/).slice(0, 2).join(" ");

let cache: Record<string, string> = existsSync(CACHE_PATH) ? JSON.parse(readFileSync(CACHE_PATH, "utf-8")) : {};
let dirty = 0;
const saveCache = () => { writeFileSync(CACHE_PATH, JSON.stringify(cache)); dirty = 0; };

const REJECT_PREFIX = /^(voucher|distribution|note|notes|type|material|specimens?|etymology|holotype|diagnosis|remarks?|locality|synonym)\b/i;
function stripHtml(s: string) { return s.replace(/<[^>]+>/g, " ").replace(/&[a-z]+;/gi, " ").replace(/\s+/g, " ").trim(); }
function qualityOk(t: string): boolean {
  if (!t) return false;
  const latin = t.replace(/[^A-Za-z]/g, ""), letters = t.replace(/[^A-Za-z\u00C0-\u024F]/g, "");
  if (letters.length && latin.length / letters.length < 0.6) return false;
  if (REJECT_PREFIX.test(t.trim())) return false;
  const words = t.split(/\s+/).filter(Boolean);
  return words.length >= 8 && /[.!?]/.test(t);
}
function firstSentences(t: string, n = 3) {
  const c = stripHtml(t); return c.split(/(?<=[.!?])\s+/).slice(0, n).join(" ").slice(0, 600);
}

async function fetchAlgae(genus: string, species: string): Promise<string> {
  const url = `${API}?genus=${encodeURIComponent(genus)}&species=${encodeURIComponent(species)}`;
  for (let a = 0; a < 3; a++) {
    try {
      const res = await fetch(url, { headers: { abapikey: KEY, Accept: "application/json" }, signal: AbortSignal.timeout(20000) });
      if (res.status === 429) { await sleep(3000 * (a + 1)); continue; }
      if (!res.ok) return "";
      const data = await res.json() as { result?: Record<string, unknown>[] } | Record<string, unknown>[];
      const rec = Array.isArray(data) ? data[0] : (data.result?.[0]);
      if (!rec) return "";
      for (const f of FIELD_CANDIDATES) {
        const v = rec[f];
        if (typeof v === "string" && v.trim()) {
          const cleaned = stripHtml(v);
          if (qualityOk(cleaned)) return firstSentences(cleaned);
        }
      }
      return "";
    } catch { if (a < 2) await sleep(1500); }
  }
  return "";
}

interface Fam { path: string; toEnrich: { idx: number; sci: string }[]; data: Record<string, unknown>; }
function scanFiles(classFilter?: string, kingdomClasses?: Set<string>): Fam[] {
  const out: Fam[] = [];
  function processFile(p: string) {
    try {
      const data = JSON.parse(readFileSync(p, "utf-8"));
      const toEnrich: { idx: number; sci: string }[] = []; let idx = 0;
      function walk(n: Record<string, unknown>) {
        if (n.rank === "SPECIES") {
          if (!((n.description as string) || "").trim()) {
            const name = (n.name as string) || "";
            if (name.includes(" ")) toEnrich.push({ idx, sci: name });
          }
          idx++;
        }
        for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
      }
      walk(data);
      if (toEnrich.length) out.push({ path: p, toEnrich, data });
    } catch { /* skip */ }
  }
  function walkDir(d: string) {
    let e: string[]; try { e = readdirSync(d); } catch { return; }
    for (const x of e) { const f = join(d, x); let st; try { st = statSync(f); } catch { continue; }
      if (st.isDirectory()) walkDir(f); else if (x.endsWith(".json") && f.includes("/src/data/")) processFile(f); }
  }
  if (classFilter) walkDir(join(root, classFilter));
  else if (kingdomClasses) for (const c of kingdomClasses) walkDir(join(root, c));
  return out;
}

function kingdomClassDirs(kingdom: string): Set<string> {
  const tax = JSON.parse(readFileSync(resolve(portalRoot, `data/taxonomy-${kingdom}.json`), "utf-8"));
  const s = new Set<string>();
  (function w(n: Record<string, unknown>) { if (n.rank === "CLASS") s.add((n.name as string).toLowerCase());
    for (const c of (n.children ?? []) as Record<string, unknown>[]) w(c); })(tax);
  return s;
}

async function main() {
  if (!KEY) {
    console.error("❌ ALGAEBASE_KEY not set. Request a key at algaebase.org, then:");
    console.error("   export ALGAEBASE_KEY=<key>");
    console.error("   npx tsx scripts/enrichFromAlgaeBase.ts --kingdom chromista");
    process.exit(1);
  }
  let classFilter = "", kingdom = "";
  for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i] === "--class") classFilter = process.argv[++i].toLowerCase();
    else if (process.argv[i] === "--kingdom") kingdom = process.argv[++i].toLowerCase();
  }
  const fams = classFilter ? scanFiles(classFilter) : scanFiles(undefined, kingdomClassDirs(kingdom || "chromista"));
  const total = fams.reduce((s, f) => s + f.toEnrich.length, 0);
  console.log(`📖 AlgaeBase enrich: ${fams.length} families · ${total} empty species\n`);
  if (!fams.length) { console.log("Nothing to do."); return; }

  let enriched = 0; const start = Date.now();
  for (let fi = 0; fi < fams.length; fi++) {
    const fam = fams[fi];
    const pending = fam.toEnrich.filter(t => cache[binomial(t.sci)] === undefined);
    for (let i = 0; i < pending.length; i += CONCURRENCY) {
      const batch = pending.slice(i, i + CONCURRENCY);
      await Promise.all(batch.map(async t => {
        const [g, s] = binomial(t.sci).split(" ");
        cache[binomial(t.sci)] = (g && s) ? await fetchAlgae(g, s) : "";
        if (++dirty >= 50) saveCache();
      }));
      await sleep(DELAY);
    }
    // apply
    const want = new Map(fam.toEnrich.map(t => [t.idx, binomial(t.sci)]));
    let idx = 0, wrote = 0;
    (function walk(n: Record<string, unknown>) {
      if (n.rank === "SPECIES") { const b = want.get(idx); if (b && cache[b]) { n.description = cache[b]; n.sourcedFrom = "algaebase"; enriched++; wrote++; } idx++; }
      for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
    })(fam.data);
    if (wrote) writeFileSync(fam.path, JSON.stringify(fam.data, null, 2) + "\n");
    if ((fi + 1) % 20 === 0 || fi === fams.length - 1) { saveCache(); console.log(`   [${fi + 1}/${fams.length}] ${enriched} enriched · ${((Date.now() - start) / 1000).toFixed(0)}s`); }
  }
  saveCache();
  console.log(`\n✅ Done — ${enriched} species enriched from AlgaeBase`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
