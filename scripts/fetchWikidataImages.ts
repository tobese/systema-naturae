/**
 * Fetch image filenames (P18 portrait, P181 range map), Commons category (P373),
 * and IUCN status (P141) from Wikidata for every species binomial we have in
 * family JSONs. Cache to shared/data/wiki-images.json.
 *
 * Strategy: query by P225 (taxon name) so we don't need QID lookups up-front.
 * Wikidata's SPARQL endpoint handles ~200 binomials per VALUES clause within
 * its 60s timeout. Sustainable rate ≈ 30 req/min; we use 1.5s spacing.
 *
 * Pushes progress to progressd as session `wikidata_images`.
 *
 * Usage:
 *   npx tsx scripts/fetchWikidataImages.ts            # full run
 *   npx tsx scripts/fetchWikidataImages.ts --limit 500
 *   npx tsx scripts/fetchWikidataImages.ts --reset    # discard cache
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const CACHE_PATH = join(ROOT, "shared", "data", "wiki-images.json");
const PROGRESSD_URL = process.env.PROGRESSD_URL || "http://localhost:9876";
const SESSION_ID = "wikidata_images";
const SESSION_LABEL = "Wikidata Image Cache";

const WDQS_URL = "https://query.wikidata.org/sparql";
const USER_AGENT =
  "systema-naturae/0.1 (https://github.com/anomalyco/systema-naturae; tb@anomaly.co) tsx-node";
const BATCH_SIZE = 200;
const BATCH_SPACING_MS = 1500;
const MAX_RETRIES = 5;

interface CacheEntry {
  qid: string;
  image?: string;
  rangeMaps?: string[];
  commonsCat?: string;
  iucnStatus?: string;
  /** ISO timestamp of last successful fetch */
  fetchedAt: string;
}

interface SparqlBinding {
  [k: string]: { type: string; value: string } | undefined;
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Walk every family JSON under repo root and collect species binomials. */
function collectBinomials(): string[] {
  const out = new Set<string>();
  const re = /^[A-Z][a-z]+ [a-z-]+$/;
  function walkNode(n: unknown) {
    if (!n || typeof n !== "object") return;
    const node = n as Record<string, unknown>;
    const name = typeof node.name === "string" ? node.name : "";
    if (re.test(name)) out.add(name);
    const children = node.children as unknown;
    if (Array.isArray(children)) for (const c of children) walkNode(c);
  }
  function walkDir(d: string) {
    let entries: string[];
    try { entries = readdirSync(d); } catch { return; }
    for (const e of entries) {
      if (e === "node_modules" || e === ".git" || e.startsWith(".")) continue;
      const full = join(d, e);
      let st;
      try { st = statSync(full); } catch { continue; }
      if (st.isDirectory()) walkDir(full);
      else if (e.endsWith(".json") && full.includes("/src/data/")) {
        try {
          const data = JSON.parse(readFileSync(full, "utf-8"));
          walkNode(data);
        } catch { /* skip unparseable */ }
      }
    }
  }
  walkDir(ROOT);
  return [...out].sort();
}

/** SPARQL query for one batch of binomials. */
function buildQuery(binomials: string[]): string {
  const values = binomials.map((b) => `"${b.replace(/"/g, '\\"')}"`).join(" ");
  return `SELECT ?species ?name ?image ?rangeMap ?commonsCat ?iucnStatus WHERE {
  VALUES ?name { ${values} }
  ?species wdt:P225 ?name .
  OPTIONAL { ?species wdt:P18 ?image }
  OPTIONAL { ?species wdt:P181 ?rangeMap }
  OPTIONAL { ?species wdt:P373 ?commonsCat }
  OPTIONAL { ?species wdt:P141 ?iucnStatus }
}`;
}

async function runQuery(binomials: string[]): Promise<SparqlBinding[]> {
  const query = buildQuery(binomials);
  let lastErr: unknown;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      // POST avoids HTTP 431 from long query strings (200 binomials + URL
      // encoding overruns Wikidata's request-line limit).
      const res = await fetch(WDQS_URL, {
        method: "POST",
        headers: {
          Accept: "application/sparql-results+json",
          "Content-Type": "application/x-www-form-urlencoded",
          "User-Agent": USER_AGENT,
        },
        body: `query=${encodeURIComponent(query)}`,
        signal: AbortSignal.timeout(60_000),
      });
      if (!res.ok) {
        // Honor Retry-After when present
        const ra = parseInt(res.headers.get("retry-after") || "0", 10);
        const wait = (ra > 0 ? ra : 2 ** attempt) * 1000;
        await sleep(wait);
        lastErr = new Error(`HTTP ${res.status}`);
        continue;
      }
      const json = (await res.json()) as { results: { bindings: SparqlBinding[] } };
      return json.results.bindings;
    } catch (e) {
      lastErr = e;
      await sleep(2 ** attempt * 1000);
    }
  }
  throw lastErr ?? new Error("query failed");
}

/** Wikidata returns one binding row per OPTIONAL hit, so we have to fold. */
function foldBindings(rows: SparqlBinding[]): Map<string, CacheEntry> {
  const out = new Map<string, CacheEntry>();
  const now = new Date().toISOString();
  for (const r of rows) {
    const name = r.name?.value;
    const qidUri = r.species?.value;
    if (!name || !qidUri) continue;
    const qid = qidUri.replace("http://www.wikidata.org/entity/", "");
    let e = out.get(name);
    if (!e) { e = { qid, fetchedAt: now }; out.set(name, e); }
    const img = r.image?.value;
    if (img && !e.image) e.image = decodeCommonsFile(img);
    const rm = r.rangeMap?.value;
    if (rm) {
      const fn = decodeCommonsFile(rm);
      e.rangeMaps ??= [];
      if (!e.rangeMaps.includes(fn)) e.rangeMaps.push(fn);
    }
    const cc = r.commonsCat?.value;
    if (cc && !e.commonsCat) e.commonsCat = cc;
    const iucn = r.iucnStatus?.value;
    if (iucn && !e.iucnStatus) {
      // IUCN status QID → short code via small inline mapping
      e.iucnStatus = IUCN_QID_TO_CODE[iucn.split("/").pop() ?? ""] ?? iucn.split("/").pop() ?? "";
    }
  }
  return out;
}

/** Wikidata returns image values as URLs into the FilePath redirect; strip to filename. */
function decodeCommonsFile(url: string): string {
  // e.g. http://commons.wikimedia.org/wiki/Special:FilePath/Lion%20distribution.png
  const last = url.split("/").pop() ?? url;
  try { return decodeURIComponent(last); } catch { return last; }
}

const IUCN_QID_TO_CODE: Record<string, string> = {
  // Verified 2026-06-27 against Wikidata's actual P141 value distribution.
  // Note: Wikidata uses Q96377276 ("Endangered status"), NOT Q11394
  // ("endangered species"), for the IUCN EN code on taxa.
  Q211005: "LC",    // Least Concern
  Q3245245: "DD",   // Data Deficient
  Q96377276: "EN",  // Endangered
  Q278113: "VU",    // Vulnerable
  Q219127: "CR",    // Critically Endangered
  Q719675: "NT",    // Near Threatened
  Q237350: "EX",    // extinct species
  Q239509: "EW",    // extinct in the wild
  Q3350324: "NE",   // not evaluated
  Q6693756: "LR",   // Lower Risk (obsolete pre-2001)
  Q11394: "EN",     // alias: "endangered species" concept (rare in P141, but safe)
};

async function pushProgress(pct: number, msg: string, done = false) {
  try {
    await fetch(`${PROGRESSD_URL}/api/sessions/${SESSION_ID}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pct, message: msg, done, label: SESSION_LABEL }),
    });
  } catch { /* progressd optional */ }
}

function loadCache(): Record<string, CacheEntry> {
  if (!existsSync(CACHE_PATH)) return {};
  try { return JSON.parse(readFileSync(CACHE_PATH, "utf-8")); } catch { return {}; }
}

function saveCache(cache: Record<string, CacheEntry>) {
  mkdirSync(dirname(CACHE_PATH), { recursive: true });
  writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2) + "\n");
}

async function main() {
  const args = process.argv.slice(2);
  const limitIdx = args.indexOf("--limit");
  const limit = limitIdx >= 0 ? parseInt(args[limitIdx + 1] ?? "0", 10) : 0;
  const reset = args.includes("--reset");

  console.log("Collecting binomials from family JSON files…");
  const all = collectBinomials();
  console.log(`  ${all.length.toLocaleString()} unique binomials`);

  const cache = reset ? {} : loadCache();
  const cached = new Set(Object.keys(cache));
  const todo = all.filter((b) => !cached.has(b));
  console.log(`  ${cached.size.toLocaleString()} already cached, ${todo.length.toLocaleString()} to fetch`);

  if (limit > 0 && todo.length > limit) {
    console.log(`  --limit ${limit}: trimming queue`);
    todo.length = limit;
  }
  if (todo.length === 0) {
    console.log("Nothing to do.");
    await pushProgress(100, `Cache complete: ${cached.size} species`, true);
    return;
  }

  await pushProgress(0, `Starting: ${todo.length} binomials to query`);

  const t0 = Date.now();
  let processed = 0;
  let withImage = 0;
  let withMap = 0;
  let saveCounter = 0;

  for (let i = 0; i < todo.length; i += BATCH_SIZE) {
    const batch = todo.slice(i, i + BATCH_SIZE);
    let folded: Map<string, CacheEntry>;
    try {
      const rows = await runQuery(batch);
      folded = foldBindings(rows);
    } catch (e) {
      console.error(`  batch ${i}/${todo.length} failed: ${(e as Error).message}`);
      processed += batch.length;
      await sleep(BATCH_SPACING_MS);
      continue;
    }

    // Record EVERY binomial we asked for (so we don't re-query misses)
    const now = new Date().toISOString();
    for (const b of batch) {
      if (folded.has(b)) {
        const e = folded.get(b)!;
        cache[b] = e;
        if (e.image) withImage++;
        if (e.rangeMaps?.length) withMap++;
      } else {
        cache[b] = { qid: "", fetchedAt: now };
      }
    }
    processed += batch.length;

    // Persist every ~20 batches (~4k species)
    if (++saveCounter % 20 === 0) saveCache(cache);

    const pct = (processed / todo.length) * 100;
    const elapsed = (Date.now() - t0) / 1000;
    const rate = processed / elapsed;
    const eta = Math.round((todo.length - processed) / Math.max(rate, 0.01));
    const msg = `${processed.toLocaleString()}/${todo.length.toLocaleString()} · img=${withImage} map=${withMap} · ${rate.toFixed(0)}/s · ETA ${Math.floor(eta / 60)}m${eta % 60}s`;
    console.log(`  ${pct.toFixed(1)}% ${msg}`);
    await pushProgress(pct, msg);

    await sleep(BATCH_SPACING_MS);
  }

  saveCache(cache);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
  const summary = `Done in ${elapsed}s · ${withImage} portraits · ${withMap} range maps`;
  console.log(summary);
  await pushProgress(100, summary, true);
}

main().catch((e) => {
  console.error("Fatal:", e);
  pushProgress(0, `Fatal: ${(e as Error).message}`, true);
  process.exit(1);
});
