/**
 * enrich_worker.mjs — pull-queue plant enrichment worker (Node, GBIF API).
 *
 * Node twin of enrich_worker.py, for tailnet boxes that have Node but not
 * Python (e.g. Steamie). Builtin fetch only — no npm install, no repo, no tsx.
 *
 * Self-serve launch:
 *   curl -s http://100.116.174.3:9881/worker.mjs -o ew.mjs
 *   node ew.mjs --server http://100.116.174.3:9881 --worker steamie
 */
import { hostname } from "os";

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_DESCR = "https://api.gbif.org/v1/species";
const UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; distributed enrich worker)";

const argv = process.argv.slice(2);
const arg = (f, d) => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const SERVER = arg("--server", "http://100.116.174.3:9881").replace(/\/$/, "");
const WORKER = arg("--worker", hostname().split(".")[0].toLowerCase());
const CONCURRENCY = Number(arg("--concurrency", "6"));
const IDLE_EXIT = Number(arg("--idle-exit", "3"));
const MAX_BATCHES = Number(arg("--max-batches", "0"));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const binomial = (n) => n.split(/\s+/).slice(0, 2).join(" ");

async function postJSON(path, obj) {
  const res = await fetch(`${SERVER}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj), signal: AbortSignal.timeout(60000),
  });
  return { status: res.status, data: res.status === 204 ? {} : await res.json().catch(() => ({})) };
}

async function gbifMatch(name) {
  const url = `${GBIF_MATCH}?name=${encodeURIComponent(name)}&strict=true`;
  const res = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(15000) });
  if (!res.ok) return null;
  const data = await res.json();
  return data.usageKey || null;
}

async function gbifDescription(key) {
  const url = `${GBIF_DESCR}/${key}/descriptions`;
  const res = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(15000) });
  if (!res.ok) return null;
  const data = await res.json();
  if (!data.results?.length) return null;
  const en = data.results.find((r) => r.language === "eng" || r.language?.startsWith("en"));
  const anyLang = data.results.find((r) => r.description?.length > 20);
  const best = en || anyLang;
  if (!best?.description) return null;
  const clean = best.description.replace(/\s+/g, " ").trim();
  return clean.length > 30 ? clean.slice(0, 500) : null;
}

async function main() {
  console.log(`[${WORKER}] polling ${SERVER} via GBIF API`);
  let total = 0, empties = 0, batches = 0;

  for (;;) {
    if (MAX_BATCHES && batches >= MAX_BATCHES) { console.log(`[${WORKER}] reached max-batches=${MAX_BATCHES}, exiting (${total} enriched)`); return; }

    let claim;
    try { claim = await postJSON("/claim", { worker: WORKER, n: 100 }); }
    catch (e) { console.log(`  claim failed (${e.message}); retry 5s`); await sleep(5000); continue; }

    const items = claim.data?.items;
    if (claim.status === 204 || !items?.length) {
      if (++empties >= IDLE_EXIT) { console.log(`[${WORKER}] queue empty — done, ${total} enriched`); return; }
      await sleep(3000); continue;
    }

    empties = 0; batches++;

    const results = [];
    let hits = 0, idx = 0;
    await Promise.all(Array.from({ length: CONCURRENCY }, async () => {
      for (;;) {
        const i = idx++;
        if (i >= items.length) break;
        const binom = binomial(items[i].name);
        let desc = null;
        try {
          // Use server-provided cached key when present: number = known GBIF key,
          // null = known no-match (skip), undefined = not cached (resolve now).
          let key = items[i].gbifKey;
          if (key === undefined) key = await gbifMatch(binom);
          if (key) desc = await gbifDescription(key);
        } catch {}
        if (desc) hits++;
        results[i] = desc ? { id: items[i].id, description: desc, sourcedFrom: "gbif" } : { id: items[i].id };
      }
    }));

    try {
      const { data } = await postJSON("/submit", { worker: WORKER, results });
      total += data.written ?? 0;
      console.log(`[${WORKER}] batch ${items.length} → ${hits} hits, +${data.written ?? 0} written (total ${total}, batch ${batches})`);
    } catch (e) { console.log(`  submit failed (${e.message}); batch re-leases`); await sleep(5000); }
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
