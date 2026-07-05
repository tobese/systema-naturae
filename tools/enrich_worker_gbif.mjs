/**
 * enrich_worker_gbif.mjs — Macie-local worker using the GBIF API for descriptions.
 *
 * Claims batches from enrichServe, matches species against GBIF, fetches
 * English descriptions, submits results. No npm packages needed.
 *
 * GBIF API docs: https://www.gbif.org/developer/species
 * Rate limit: very generous (up to ~10-20 req/s, but we go easy).
 *
 * Usage:
 *   node tools/enrich_worker_gbif.mjs
 */
const SERVER = "http://localhost:9881";
const WORKER = "macie-gbif";
const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_DESCR = "https://api.gbif.org/v1/species";
const UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; GBIF enrich worker)";
const CONCURRENCY = 8;
const DELAY = 200;
const IDLE_EXIT = 3;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const binomial = (n) => n.split(/\s+/).slice(0, 2).join(" ");

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

async function lookupOne(name) {
  try {
    const key = await gbifMatch(name);
    if (!key) return null;
    return await gbifDescription(key);
  } catch {
    return null;
  }
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
  console.log(`[${WORKER}] polling ${SERVER} via GBIF API`);
  let total = 0, empties = 0, batches = 0;

  for (;;) {
    let claim;
    try {
      claim = await postJSON("/claim", { worker: WORKER, n: 100 });
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

    const names = items.map((it) => binomial(it.name));
    const results = [];
    let hits = 0;

    // Concurrent lookups
    const queues = Array.from({ length: CONCURRENCY }, (_, i) => i);
    let idx = 0;
    await Promise.all(queues.map(async () => {
      for (;;) {
        const i = idx++;
        if (i >= items.length) break;
        const desc = await lookupOne(names[i]);
        if (desc) hits++;
        results[i] = desc ? { id: items[i].id, description: desc, sourcedFrom: "gbif" } : { id: items[i].id };
        if (i > 0 && i % (CONCURRENCY * 5) === 0) await sleep(100);
      }
    }));

    try {
      const { data } = await postJSON("/submit", { worker: WORKER, results });
      total += data.written ?? 0;
      console.log(`[${WORKER}] batch ${items.length} → ${hits} hits, +${data.written ?? 0} written (total ${total}, batch ${batches})`);
    } catch (e) {
      console.log(`  submit failed (${e.message}); batch re-leases`);
      await sleep(5000);
    }

    await sleep(DELAY);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
