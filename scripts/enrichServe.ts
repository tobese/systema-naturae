/**
 * enrichServe — Macie-side pull queue for distributed plant enrichment.
 *
 * Modeled on snedtankt's receive.py: workers on the tailnet POST /claim to
 * lease a batch of un-enriched species, enrich them locally (Wikipedia REST
 * from their own IP), then POST /submit the results. Macie is the ONLY writer
 * to the family JSONs — no repo, no git, no ssh needed on the workers, and no
 * write races. Claims carry a lease; a crashed worker's batch falls back into
 * the pool automatically.
 *
 * Usage: node --max-old-space-size=4096 (via tsx) scripts/enrichServe.ts [--port 9881]
 *
 *   POST /claim   { worker, n? }        → { items: [{id, name}], ... } | 204 empty
 *   POST /submit  { worker, results:[{id, description, commonName?}] } → { written }
 *   GET  /status                        → counts (json)
 *   GET  /worker.py                     → the Python worker source (self-serve)
 *   GET  /health                        → { ok, total, done }
 */
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "fs";
import { resolve, dirname, join, sep } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";
import { createServer } from "http";

const SQLITE_DB = "/Volumes/WikiDump/wiki-pages-plants.sqlite";
const SQLITE_FALLBACK = "/Volumes/WikiDump/wiki-pages.sqlite";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const CLASSES = ["liliopsida", "magnoliopsida"];
const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+/;

const argv = process.argv.slice(2);
const arg = (f: string, d: string) => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const PORT = Number(arg("--port", "9881"));
const BATCH = Number(arg("--batch", "50"));
const LEASE_MS = Number(arg("--lease-ms", "600000"));      // 10 min
const FLUSH_MS = Number(arg("--flush-ms", "60000"));       // write dirty files every 60s
const PUSH_MS = Number(arg("--push-ms", "900000"));        // git push every 15 min / on drain
const PROGRESS_ID = arg("--progress-id", "plant-enrich-2026-07-05");
const PROGRESSD = arg("--progressd", "http://localhost:9876").replace(/\/$/, "");
const WORKER_PY = resolve(root, "tools", "enrich_worker.py");
const WORKER_MJS = resolve(root, "tools", "enrich_worker.mjs");

interface Cand { id: number; name: string; file: string; node: any; status: 0 | 1 | 2; worker?: string; at?: number } // 0 queued 1 leased 2 done

// --- load every family tree into memory; collect un-enriched candidates ------
const files: string[] = (() => {
  const needle = `${sep}src${sep}data${sep}`;
  const out: string[] = [];
  const walk = (d: string) => {
    let es: string[]; try { es = readdirSync(d); } catch { return; }
    for (const n of es) {
      const p = join(d, n);
      let st; try { st = statSync(p); } catch { continue; }
      if (st.isDirectory()) walk(p);
      else if (p.endsWith(".json") && p.includes(needle)) out.push(p);
    }
  };
  for (const c of CLASSES) { const b = resolve(root, c); if (existsSync(b)) walk(b); }
  return out.sort();
})();

const trees = new Map<string, any>();
const pool: Cand[] = [];
let nextId = 0;
for (const f of files) {
  let d; try { d = JSON.parse(readFileSync(f, "utf-8")); } catch { continue; }
  trees.set(f, d);
  (function walk(n: any) {
    if (n.rank === "SPECIES") {
      const done = n.sourcedFrom === "none" || ((n.sourcedFrom === "wikipedia" || n.sourcedFrom === "gbif") && (n.description?.length ?? 0) > 40);
      if (!done && BINOMIAL_RE.test(n.name ?? "")) pool.push({ id: nextId++, name: n.name, file: f, node: n, status: 0 });
      return;
    }
    for (const c of n.children ?? []) walk(c);
  })(d);
}
const total = pool.length;
let doneCount = 0;
const dirty = new Set<string>();
const perWorker = new Map<string, number>();
console.log(`enrichServe: ${trees.size} families, ${total.toLocaleString()} candidates queued`);

// --- server-side SQLite enrichment pass (no network calls) --------------------
function enrichFromSqlite() {
  // Dump extract for ALL pages from both DBs into memory in one shot
  const extractByTitle = new Map<string, string>();
  for (const dbPath of [SQLITE_DB, SQLITE_FALLBACK]) {
    if (!existsSync(dbPath)) continue;
    const r = spawnSync("sqlite3", ["-json", dbPath, "SELECT title, extract FROM pages WHERE extract IS NOT NULL AND length(extract) > 30;"], { encoding: "utf-8", timeout: 120000, maxBuffer: 200 * 1024 * 1024 });
    if (r.status !== 0 || !r.stdout) continue;
    try {
      const rows = JSON.parse(r.stdout);
      for (const row of rows) {
        if (!extractByTitle.has(row.title)) {
          const desc = row.extract.replace(/\n+/g, " ").trim();
          const firstSentences = desc.split(/(?<=[.!?])\s+/).slice(0, 3).join(" ");
          extractByTitle.set(row.title, firstSentences.length > 30 ? firstSentences : desc);
        }
      }
    } catch {}
  }
  if (!extractByTitle.size) return;
  console.log(`[sqlite] loaded ${extractByTitle.size} extracts from DB`);

  // Match candidates in-memory
  let matched = 0;
  for (const c of pool) {
    if (c.status !== 0) continue;
    const b = c.name.split(/\s+/).slice(0, 2).join(" ");
    if (!b) continue;
    const desc = extractByTitle.get(b);
    if (!desc) continue;
    c.node.description = desc.slice(0, 500);
    c.node.sourcedFrom = "wikipedia";
    c.status = 2;
    doneCount++;
    matched++;
    dirty.add(c.file);
  }
  console.log(`[sqlite] enriched ${matched} candidates from ${extractByTitle.size} extracts`);
}
if (existsSync(SQLITE_DB) || existsSync(SQLITE_FALLBACK)) {
  console.log("enrichServe: running server-side SQLite pass…");
  enrichFromSqlite();
  flush();
  console.log(`enrichServe: ${doneCount}/${total} enriched from SQLite, ${pool.filter(c => c.status === 0).length.toLocaleString()} remaining for workers`);
}

// --- queue ops ---------------------------------------------------------------
let cursor = 0;
function sweep() {
  const now = Date.now();
  for (const c of pool) if (c.status === 1 && now - (c.at ?? 0) > LEASE_MS) { c.status = 0; c.worker = undefined; }
}
function claim(worker: string, n: number): Cand[] {
  sweep();
  const out: Cand[] = [];
  // fast path from cursor, then wrap once to catch released leases
  let scanned = 0;
  while (out.length < n && scanned < pool.length) {
    const c = pool[cursor];
    cursor = (cursor + 1) % pool.length;
    scanned++;
    if (c.status === 0) { c.status = 1; c.worker = worker; c.at = Date.now(); out.push(c); }
  }
  return out;
}

// --- persistence -------------------------------------------------------------
function flush() {
  if (dirty.size === 0) return;
  const paths = [...dirty]; dirty.clear();
  for (const p of paths) {
    const t = trees.get(p); if (!t) continue;
    try { writeFileSync(p, JSON.stringify(t, null, 2) + "\n"); } catch (e) { console.error(`flush ${p}: ${(e as Error).message}`); }
  }
  const git = (...a: string[]) => spawnSync("git", a, { cwd: root, encoding: "utf-8" });
  git("add", "--", ...CLASSES);
  if (git("diff", "--cached", "--quiet").status !== 0) {
    git("commit", "-m", `enrich: Tier-2 queue submit — ${doneCount}/${total} (${paths.length} files)`);
    console.log(`committed (${paths.length} files, ${doneCount}/${total} done)`);
  }
}
let lastPush = Date.now();
function maybePush(force = false) {
  if (!force && Date.now() - lastPush < PUSH_MS) return;
  lastPush = Date.now();
  const p = spawnSync("git", ["push", "origin", "main"], { cwd: root, encoding: "utf-8" });
  console.log(p.status === 0 ? "pushed to main" : `push failed: ${p.stderr?.slice(0, 200)}`);
}
async function postProgress() {
  try {
    await fetch(`${PROGRESSD}/api/sessions/${PROGRESS_ID}/progress`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: `queue: ${doneCount}/${total} enriched (${[...perWorker].map(([w, c]) => `${w}:${c}`).join(" ")})`, pct: total ? Math.round((doneCount / total) * 100) : 100 }),
      signal: AbortSignal.timeout(5000),
    });
  } catch {}
}
setInterval(() => { flush(); maybePush(); postProgress(); }, FLUSH_MS);

// --- server-side GBIF enrichment loop (caches results locally) ---------------
const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_DESCR = "https://api.gbif.org/v1/species";
const GBIF_UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; enrichServe)";
const GBIF_CONCURRENCY = 8;

async function gbifMatch(name: string): Promise<number | null> {
  try {
    const url = `${GBIF_MATCH}?name=${encodeURIComponent(name)}&strict=true`;
    const res = await fetch(url, { headers: { "User-Agent": GBIF_UA }, signal: AbortSignal.timeout(15000) });
    if (!res.ok) return null;
    const data: any = await res.json();
    return data.usageKey || null;
  } catch { return null; }
}

async function gbifDescription(key: number): Promise<string | null> {
  try {
    const url = `${GBIF_DESCR}/${key}/descriptions`;
    const res = await fetch(url, { headers: { "User-Agent": GBIF_UA }, signal: AbortSignal.timeout(15000) });
    if (!res.ok) return null;
    const data: any = await res.json();
    if (!data.results?.length) return null;
    const en = data.results.find((r: any) => r.language === "eng" || r.language?.startsWith("en"));
    const anyLang = data.results.find((r: any) => r.description?.length > 20);
    const best = en || anyLang;
    if (!best?.description) return null;
    const clean = best.description.replace(/\s+/g, " ").trim();
    return clean.length > 30 ? clean.slice(0, 500) : null;
  } catch { return null; }
}

async function gbifEnrichBatch() {
  // Claim items from the pool directly (synthetic "server" worker)
  sweep();
  const batch: Cand[] = [];
  let scanned = 0;
  while (batch.length < 100 && scanned < pool.length) {
    const c = pool[cursor];
    cursor = (cursor + 1) % pool.length;
    scanned++;
    if (c.status === 0) { c.status = 1; c.at = Date.now(); c.worker = "server-gbif"; batch.push(c); }
  }
  if (!batch.length) return;

  let written = 0;
  let idx = 0;
  await Promise.all(Array.from({ length: GBIF_CONCURRENCY }, async () => {
    for (;;) {
      const i = idx++;
      if (i >= batch.length) break;
      const c = batch[i];
      const binom = c.name.split(/\s+/).slice(0, 2).join(" ");
      let ok = false;
      try {
        const key = await gbifMatch(binom);
        if (key) {
          const desc = await gbifDescription(key);
          if (desc) {
            c.node.description = desc;
            c.node.sourcedFrom = "gbif";
            c.status = 2;
            doneCount++;
            written++;
            dirty.add(c.file);
            ok = true;
          }
        }
      } catch {}
      if (!ok) {
        c.node.sourcedFrom = "none";
        c.status = 2;
        doneCount++;
        dirty.add(c.file);
      }
    }
  }));
  if (written) console.log(`[server-gbif] batch ${batch.length} → +${written} enriched (total ${doneCount}/${total})`);
}

// Run a GBIF batch every 30s (between flush intervals)
const GBIF_RUN_MS = 30000;
function scheduleGbif() {
  gbifEnrichBatch().catch(() => {}).then(() => setTimeout(scheduleGbif, GBIF_RUN_MS));
}
if (pool.length > 0) setTimeout(scheduleGbif, 5000);

// --- http --------------------------------------------------------------------
function body(req: any): Promise<any> {
  return new Promise((res) => { let b = ""; req.on("data", (c: any) => (b += c)); req.on("end", () => { try { res(JSON.parse(b || "{}")); } catch { res({}); } }); });
}
const server = createServer(async (req, res) => {
  const send = (s: number, o: any) => { res.writeHead(s, { "Content-Type": "application/json" }); res.end(JSON.stringify(o)); };
  try {
    if (req.method === "GET" && req.url === "/health") return send(200, { ok: true, total, done: doneCount });
    if (req.method === "GET" && req.url === "/status")
      return send(200, { total, done: doneCount, leased: pool.filter(c => c.status === 1).length, queued: pool.filter(c => c.status === 0).length, workers: Object.fromEntries(perWorker) });
    if (req.method === "GET" && (req.url === "/worker.py" || req.url === "/worker.mjs")) {
      const f = req.url === "/worker.mjs" ? WORKER_MJS : WORKER_PY;
      const src = existsSync(f) ? readFileSync(f, "utf-8") : "// worker not found";
      res.writeHead(200, { "Content-Type": "text/plain" }); return res.end(src);
    }
    if (req.method === "POST" && req.url === "/claim") {
      const { worker = "anon", n = BATCH } = await body(req);
      const items = claim(worker, Math.min(Number(n) || BATCH, 200));
      if (items.length === 0) return send(204, {});
      return send(200, { items: items.map(c => ({ id: c.id, name: c.name })), lease_ms: LEASE_MS });
    }
    if (req.method === "POST" && req.url === "/submit") {
      const { worker = "anon", results = [] } = await body(req);
      let written = 0;
      for (const r of results) {
        const c = pool[r.id];
        if (!c || c.status === 2) continue;
        if (r.description && r.description.length > 20) {
          c.node.description = r.description;
          c.node.sourcedFrom = r.sourcedFrom || "wikipedia";
          if (r.commonName) c.node.commonName = r.commonName;
          c.status = 2; doneCount++; dirty.add(c.file); written++;
        } else {
          c.node.sourcedFrom = "none";
          c.status = 2;
          doneCount++; dirty.add(c.file);
        }
      }
      if (written) perWorker.set(worker, (perWorker.get(worker) ?? 0) + written);
      if (pool.every(c => c.status === 2)) { flush(); maybePush(true); console.log("QUEUE DRAINED"); }
      return send(200, { written });
    }
    send(404, { error: "not found" });
  } catch (e) { send(500, { error: (e as Error).message }); }
});
server.listen(PORT, () => console.log(`enrichServe on :${PORT}  (/claim /submit /status /worker.py)  batch=${BATCH} lease=${LEASE_MS}ms`));

process.on("SIGINT", () => { console.log("\nflushing + pushing before exit…"); flush(); maybePush(true); process.exit(0); });
