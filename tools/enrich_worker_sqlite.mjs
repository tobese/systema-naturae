/**
 * enrich_worker_sqlite.mjs — Macie-local worker using the offline Wikipedia SQLite DB.
 *
 * Claims batches from enrichServe, looks up species in the SQLite dump via
 * the system sqlite3 CLI (bulk JSON queries), submits results.
 * No npm packages needed.
 *
 * Usage:
 *   node tools/enrich_worker_sqlite.mjs
 */
import { spawnSync } from "child_process";

const SERVER = "http://localhost:9881";
const WORKER = "macie-sqlite";
const DELAY = 50;
const IDLE_EXIT = 3;
const DB = "/Volumes/WikiDump/wiki-pages-plants.sqlite";
const FALLBACK_DB = "/Volumes/WikiDump/wiki-pages.sqlite";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const binomial = (n) => n.split(/\s+/).slice(0, 2).join(" ");

function firstSentences(text, n = 3) {
  if (!text) return null;
  const clean = text.replace(/\n+/g, " ").trim();
  const s = clean.split(/(?<=[.!?])\s+/).slice(0, n).join(" ");
  return s.length > 30 ? s : clean.length > 30 ? clean : null;
}

/** Bulk-lookup many binomials in a SQLite DB. Returns Map<binomial, description>. */
function bulkLookup(dbPath, names) {
  const bins = [...new Set(names.map(binomial).filter(Boolean))];
  if (!bins.length) return new Map();
  const sql = `SELECT title, extract FROM pages WHERE title IN (${bins.map(b => `'${b.replace(/'/g, "''")}'`).join(",")});`;
  const r = spawnSync("sqlite3", ["-json", dbPath, sql], { encoding: "utf-8", timeout: 30000, maxBuffer: 50 * 1024 * 1024 });
  if (r.status !== 0 || !r.stdout) return new Map();
  const map = new Map();
  try {
    const rows = JSON.parse(r.stdout);
    for (const row of rows) {
      const desc = firstSentences(row.extract);
      if (desc) map.set(row.title, desc);
    }
  } catch {}
  return map;
}

async function postJSON(path, obj) {
  const res = await fetch(`${SERVER}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj),
    signal: AbortSignal.timeout(60000),
  });
  return { status: res.status, data: res.status === 204 ? {} : await res.json().catch(() => ({})) };
}

async function main() {
  console.log(`[${WORKER}] polling ${SERVER} via SQLite DBs (${DB}, ${FALLBACK_DB})`);
  let total = 0, empties = 0, batches = 0;

  for (;;) {
    let claim;
    try {
      claim = await postJSON("/claim", { worker: WORKER, n: 200 });
    } catch (e) {
      console.log(`  claim failed (${e.message}); retry 5s`);
      await sleep(5000);
      continue;
    }

    const items = claim.data?.items;
    if (claim.status === 204 || !items?.length) {
      if (++empties >= IDLE_EXIT) {
        console.log(`[${WORKER}] queue empty — done, ${total} enriched (${batches} batches)`);
        return;
      }
      await sleep(3000);
      continue;
    }

    empties = 0;
    batches++;

    const names = items.map(it => it.name);
    const primaryMap = bulkLookup(DB, names);
    const missing = names.filter(n => !primaryMap.has(binomial(n)));
    const fallbackMap = missing.length > 0 ? bulkLookup(FALLBACK_DB, missing) : new Map();

    const results = items.map(it => {
      const binom = binomial(it.name);
      const desc = primaryMap.get(binom) || fallbackMap.get(binom);
      return desc ? { id: it.id, description: desc } : { id: it.id };
    });

    try {
      const { data } = await postJSON("/submit", { worker: WORKER, results });
      total += data.written ?? 0;
      const hits = results.filter(r => r.description).length;
      console.log(`[${WORKER}] batch ${items.length} → ${hits} hits, +${data.written ?? 0} written (total ${total}, batch ${batches})`);
    } catch (e) {
      console.log(`  submit failed (${e.message}); batch re-leases`);
      await sleep(5000);
    }

    await sleep(DELAY);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
