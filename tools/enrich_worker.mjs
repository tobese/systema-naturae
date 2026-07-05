/**
 * enrich_worker.mjs — pull-queue plant enrichment worker (Node, Tier-2 REST).
 *
 * Node twin of enrich_worker.py, for tailnet boxes that have Node but not
 * Python (e.g. Steamie). Builtin fetch only — no npm install, no repo, no tsx.
 *
 * Self-serve launch:
 *   curl -s http://100.116.174.3:9881/worker.mjs -o ew.mjs
 *   node ew.mjs --server http://100.116.174.3:9881 --worker steamie
 */
import { hostname } from "os";

const WIKI_API = "https://en.wikipedia.org/w/api.php";
const UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; distributed enrich worker)";

const argv = process.argv.slice(2);
const arg = (f, d) => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const SERVER = arg("--server", "http://100.116.174.3:9881").replace(/\/$/, "");
const WORKER = arg("--worker", hostname().split(".")[0].toLowerCase());
const DELAY = Number(arg("--delay", "1.5")) * 1000;
const IDLE_EXIT = Number(arg("--idle-exit", "3"));
const MAX_BATCHES = Number(arg("--max-batches", "0"));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const binomial = (n) => n.split(/\s+/).slice(0, 2).join(" ");

async function postJSON(path, obj) {
  const res = await fetch(`${SERVER}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj), signal: AbortSignal.timeout(20000),
  });
  return { status: res.status, data: res.status === 204 ? {} : await res.json().catch(() => ({})) };
}

/** → { results: Map<name,{description,commonName?}>, limited: bool } */
async function fetchWikipedia(names) {
  const results = new Map();
  const bins = [...new Set(names.map(binomial).filter(Boolean))];
  if (!bins.length) return { results, limited: false };
  const params = new URLSearchParams({
    action: "query", titles: bins.join("|"), prop: "extracts", exintro: "1",
    explaintext: "1", exlimit: String(Math.min(bins.length, 50)), redirects: "1", format: "json",
  });
  let data;
  try {
    const res = await fetch(`${WIKI_API}?${params}`, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(20000) });
    if (res.status === 429) { console.log(`  429 rate-limited (Retry-After=${res.headers.get("retry-after") || "?"})`); return { results, limited: true }; }
    if (!res.ok) { console.log(`  wiki fetch failed: HTTP ${res.status}`); return { results, limited: false }; }
    data = await res.json();
  } catch (e) { console.log(`  wiki fetch failed: ${e.message}`); return { results, limited: false }; }
  const pages = data.query?.pages ?? {};
  const redir = new Map();
  for (const r of data.query?.redirects ?? []) redir.set(r.from, r.to);
  for (const r of data.query?.normalized ?? []) if (!redir.has(r.from)) redir.set(r.from, r.to);
  const titleId = new Map();
  for (const [id, p] of Object.entries(pages)) if (!p.missing) titleId.set(p.title, id);
  for (const name of names) {
    const b = binomial(name);
    const id = titleId.get(redir.get(b) ?? b);
    if (id == null) continue;
    const p = pages[id];
    const extract = (p.extract || "").replace(/<[^>]+>/g, "").trim();
    if (!extract) continue;
    const first = extract.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ");
    const out = { description: first.length > 50 ? first : extract };
    if (p.description && p.description.length < 80) out.commonName = p.description;
    results.set(name, out);
  }
  return { results, limited: false };
}

async function main() {
  console.log(`[${WORKER}] polling ${SERVER}`);
  let total = 0, empties = 0, backoff = 0, batches = 0;
  for (;;) {
    if (MAX_BATCHES && batches >= MAX_BATCHES) { console.log(`[${WORKER}] reached max-batches=${MAX_BATCHES}, exiting (${total} enriched)`); return; }
    let claim;
    try { claim = await postJSON("/claim", { worker: WORKER }); }
    catch (e) { console.log(`  claim failed (${e.message}); retry 5s`); await sleep(5000); continue; }
    const items = claim.data?.items;
    if (claim.status === 204 || !items?.length) {
      if (++empties >= IDLE_EXIT) { console.log(`[${WORKER}] queue empty — done, ${total} enriched`); return; }
      await sleep(3000); continue;
    }
    empties = 0; batches++;
    const { results, limited } = await fetchWikipedia(items.map((it) => it.name));
    if (limited) {
      await postJSON("/submit", { worker: WORKER, results: items.map((it) => ({ id: it.id })) }).catch(() => {});
      backoff = backoff ? Math.min(backoff * 2, 300) : 15;
      console.log(`[${WORKER}] backing off ${backoff}s (rate limited)`);
      await sleep(backoff * 1000); continue;
    }
    backoff = 0;
    const out = items.map((it) => {
      const r = results.get(it.name);
      return r ? { id: it.id, description: r.description, ...(r.commonName ? { commonName: r.commonName } : {}) } : { id: it.id };
    });
    try {
      const { data } = await postJSON("/submit", { worker: WORKER, results: out });
      total += data.written ?? 0;
      console.log(`[${WORKER}] batch ${items.length} → +${data.written ?? 0} enriched (total ${total})`);
    } catch (e) { console.log(`  submit failed (${e.message}); batch re-leases`); await sleep(5000); }
    await sleep(DELAY);
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
