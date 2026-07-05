/**
 * enrichWorker — distributed, cross-platform plant enrichment worker.
 *
 * Every worker runs the SAME deterministic pre-scan + bin-pack over all plant
 * family files, then processes only its own shard (--shard k/N). Because the
 * partition is a pure function of the file set, every machine computes an
 * identical, disjoint split with no coordinator state to pass around.
 *
 * Tier 1: batched lookup against Macie's dbserved (--db-url).
 * Tier 2: Wikipedia REST fallback from this worker's own IP (--live).
 * Writes enriched family JSON in place (on the shared SMB mount).
 * Posts progress to progressd keyed by hostname.
 *
 * Usage:
 *   npx tsx scripts/enrichWorker.ts --shard 0/1 [--live] \
 *     [--db-url http://macie.local:9877] [--progressd http://macie.local:9876]
 *
 * Dry-run on Macie alone: --shard 0/1 --db-url http://localhost:9880
 */
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "fs";
import { resolve, dirname, join, sep } from "path";
import { fileURLToPath } from "url";
import { hostname } from "os";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const CLASSES = ["liliopsida", "magnoliopsida"];
const WIKI_API = "https://en.wikipedia.org/w/api.php";
const BATCH_SIZE = 50;
const DELAY_MS = 1500;
const HOST = hostname().split(".")[0].toUpperCase();

const argv = process.argv.slice(2);
const arg = (flag: string, def: string) => {
  const i = argv.indexOf(flag);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : def;
};
const has = (flag: string) => argv.includes(flag);

const [shardK, shardN] = arg("--shard", "0/1").split("/").map(Number);
const LIMIT = Number(arg("--limit", "0")); // 0 = no limit; cap families (for dry-runs)
const LIVE = has("--live");
const DB_URL = arg("--db-url", "http://localhost:9880").replace(/\/$/, "");
const PROGRESSD = arg("--progressd", "http://localhost:9876").replace(/\/$/, "");
const PROGRESS_ID = arg("--progress-id", "plant-enrich-2026-07-05");

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const binomial = (n: string) => n.split(/\s+/).slice(0, 2).join(" ");
const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+/;

/** Recursive walk (cross-platform; no `find`). Collects src/data/<x>.json files. */
function collectFamilyFiles(): string[] {
  const needle = `${sep}src${sep}data${sep}`;
  const out: string[] = [];
  const walk = (d: string) => {
    let entries: string[];
    try {
      entries = readdirSync(d);
    } catch {
      return;
    }
    for (const name of entries) {
      const p = join(d, name);
      let st;
      try {
        st = statSync(p);
      } catch {
        continue;
      }
      if (st.isDirectory()) walk(p);
      else if (p.endsWith(".json") && p.includes(needle)) out.push(p);
    }
  };
  for (const cls of CLASSES) {
    const base = resolve(root, cls);
    if (existsSync(base)) walk(base);
  }
  return out.sort(); // deterministic across machines
}

interface Fam { path: string; name: string; candCount: number }

/** Count species that still need enrichment (mirrors enrichPlantae skip logic). */
function candidateCount(node: any): number {
  let c = 0;
  const walk = (n: any) => {
    if (n.rank === "SPECIES") {
      const done = n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40;
      if (!done && BINOMIAL_RE.test(n.name ?? "")) c++;
      return;
    }
    for (const ch of n.children ?? []) walk(ch);
  };
  walk(node);
  return c;
}

/** Longest-processing-time greedy bin-pack → N balanced buckets by candidate count. */
function shardFamilies(fams: Fam[]): Fam[] {
  const buckets: { load: number; fams: Fam[] }[] = Array.from({ length: shardN }, () => ({ load: 0, fams: [] }));
  for (const f of [...fams].sort((a, b) => b.candCount - a.candCount || a.path.localeCompare(b.path))) {
    const lightest = buckets.reduce((m, b) => (b.load < m.load ? b : m), buckets[0]);
    lightest.fams.push(f);
    lightest.load += f.candCount;
  }
  return buckets[shardK].fams;
}

async function dbLookup(keys: string[]): Promise<Map<string, { extract: string; description?: string }>> {
  const map = new Map<string, { extract: string; description?: string }>();
  if (keys.length === 0) return map;
  try {
    const res = await fetch(`${DB_URL}/lookup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keys }),
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) return map;
    const data = (await res.json()) as Record<string, { extract: string; description?: string }>;
    for (const [k, v] of Object.entries(data)) map.set(k, v);
  } catch (e) {
    console.error(`  dbserved lookup failed: ${(e as Error).message}`);
  }
  return map;
}

async function fetchLive(names: string[]): Promise<Map<string, { extract: string; description?: string }>> {
  const result = new Map<string, { extract: string; description?: string }>();
  const bins = [...new Set(names.map(binomial).filter(Boolean))];
  if (bins.length === 0) return result;
  const params = new URLSearchParams({
    action: "query", titles: bins.join("|"),
    prop: "extracts", exintro: "1", explaintext: "1",
    exlimit: String(Math.min(bins.length, BATCH_SIZE)),
    redirects: "1", format: "json", origin: "*",
  });
  let data: any;
  try {
    const res = await fetch(`${WIKI_API}?${params}`, {
      headers: { "User-Agent": "SystemaNaturae/1.0 (distributed enrich worker)" },
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return result;
    data = await res.json();
  } catch {
    return result;
  }
  const pages = data.query?.pages ?? {};
  const redirects = new Map<string, string>();
  for (const r of data.query?.redirects ?? []) redirects.set(r.from, r.to);
  for (const r of data.query?.normalized ?? []) if (!redirects.has(r.from)) redirects.set(r.from, r.to);
  const lookup = new Map<string, number>();
  for (const [id, page] of Object.entries(pages)) {
    const p = page as any;
    if (!p.missing) lookup.set(p.title, Number(id));
  }
  for (const name of names) {
    const bin = binomial(name);
    const id = lookup.get(redirects.get(bin) ?? bin);
    if (id == null) continue;
    const p = pages[id] as any;
    if (!p.extract) continue;
    const extract = p.extract.replace(/<[^>]+>/g, "").trim();
    const first = extract.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ");
    result.set(name, {
      extract: first.length > 50 ? first : extract,
      description: p.description?.length < 80 ? p.description : undefined,
    });
  }
  return result;
}

async function progressd(path: string, body?: object) {
  try {
    await fetch(`${PROGRESSD}/api/sessions/${PROGRESS_ID}/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...(body ? { body: JSON.stringify(body) } : {}),
      signal: AbortSignal.timeout(5000),
    });
  } catch {}
}
const postProgress = (message: string, pct?: number) =>
  progressd("progress", { message, ...(pct !== undefined ? { pct } : {}) });

async function main() {
  console.log(`[${HOST}] shard ${shardK}/${shardN}  live=${LIVE}  db=${DB_URL}`);

  const files = collectFamilyFiles();
  const allFams: Fam[] = [];
  for (const fp of files) {
    try {
      const d = JSON.parse(readFileSync(fp, "utf-8"));
      const cc = candidateCount(d);
      if (cc > 0) allFams.push({ path: fp, name: d.name, candCount: cc });
    } catch {}
  }
  const totalCand = allFams.reduce((s, f) => s + f.candCount, 0);
  let mine = shardFamilies(allFams);
  if (LIMIT > 0) mine = mine.slice(0, LIMIT);
  const myCand = mine.reduce((s, f) => s + f.candCount, 0);
  console.log(`[${HOST}] ${allFams.length} families / ${totalCand} candidates total → my shard: ${mine.length} families / ${myCand} candidates`);
  await postProgress(`${HOST}: starting shard ${shardK}/${shardN} — ${mine.length} fams, ${myCand} candidates`, 0);

  let ok = 0, apiCalls = 0;

  for (let fi = 0; fi < mine.length; fi++) {
    const fam = mine[fi];
    const data = JSON.parse(readFileSync(fam.path, "utf-8"));

    const cand: any[] = [];
    const walk = (n: any) => {
      if (n.rank === "SPECIES") {
        const done = n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40;
        if (!done && BINOMIAL_RE.test(n.name ?? "")) cand.push(n);
        return;
      }
      for (const c of n.children ?? []) walk(c);
    };
    walk(data);
    if (cand.length === 0) continue;

    let famOk = 0;

    // Tier 1 — dbserved (batched)
    const keys = [...new Set(cand.map((n) => binomial(n.name).toLowerCase()))];
    const dbHits = await dbLookup(keys);
    for (const n of cand) {
      const hit = dbHits.get(binomial(n.name).toLowerCase());
      if (hit && hit.extract?.length > 20) {
        n.description = hit.extract;
        n.sourcedFrom = "wikipedia";
        if (hit.description) n.commonName = hit.description;
        famOk++;
      }
    }

    // Tier 2 — Wikipedia REST fallback (own IP)
    if (LIVE) {
      const remaining = cand.filter((n) => n.sourcedFrom !== "wikipedia");
      for (let i = 0; i < remaining.length; i += BATCH_SIZE) {
        const batch = remaining.slice(i, i + BATCH_SIZE);
        await sleep(DELAY_MS);
        apiCalls++;
        const live = await fetchLive(batch.map((n) => n.name));
        for (const n of batch) {
          const r = live.get(n.name);
          if (!r) continue;
          n.description = r.extract;
          n.sourcedFrom = "wikipedia";
          if (r.description) n.commonName = r.description;
          famOk++;
        }
      }
    }

    if (famOk > 0) writeFileSync(fam.path, JSON.stringify(data, null, 2) + "\n");
    ok += famOk;

    const pct = myCand > 0 ? Math.round((ok / myCand) * 100) : 100;
    console.log(`[${HOST}] [${fi + 1}/${mine.length}] ${fam.name}: +${famOk} (${ok}/${myCand}, ${pct}%)`);
    if (fi % 5 === 0 || fi === mine.length - 1) {
      await postProgress(`${HOST}: ${fi + 1}/${mine.length} fams, ${ok}/${myCand} enriched`, pct);
    }
  }

  const final = `${HOST}: DONE — ${ok}/${myCand} enriched (+${apiCalls} API calls), shard ${shardK}/${shardN}`;
  console.log(`\n${final}`);
  await postProgress(final, 100);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
