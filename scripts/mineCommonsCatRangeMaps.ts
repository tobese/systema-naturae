/**
 * mineCommonsCatRangeMaps — for every species in shared/data/wiki-images.json
 * that has a `commonsCat` but no `rangeMaps[]`, ask the Commons API which
 * files live in that category, then filter for files whose names look like
 * range / distribution maps and merge them back into the cache.
 *
 * Phase 1 step in the habitat-map upgrade: drains the cheapest pool of
 * unrecovered range maps (cats already indexed by Wikidata) before we
 * fall back to processing the 12 GB commonswiki-categorylinks.sql.gz.
 *
 * Pushes progress to phylumProgressd (localhost:9876) as session
 * `commons_cat_range_mining` so the run is visible alongside other
 * long-running fetches.
 *
 * Usage:
 *   npx tsx scripts/mineCommonsCatRangeMaps.ts                # full run
 *   npx tsx scripts/mineCommonsCatRangeMaps.ts --limit 100    # sample
 *   npx tsx scripts/mineCommonsCatRangeMaps.ts --dry-run      # don't write
 *   npx tsx scripts/mineCommonsCatRangeMaps.ts --concurrency 8
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const CACHE_PATH = join(ROOT, "shared", "data", "wiki-images.json");
const PROGRESSD_URL = process.env.PROGRESSD_URL || "http://localhost:9876";
const SESSION_ID = "commons_cat_range_mining";
const SESSION_LABEL = "Commons commonsCat range-map mining";

const API_URL = "https://commons.wikimedia.org/w/api.php";
const USER_AGENT =
  "systema-naturae/0.1 (https://github.com/anomalyco/systema-naturae; tb@anomaly.co) range-map-miner";

const DEFAULT_CONCURRENCY = 3;
const MAX_RETRIES = 4;
const SAVE_EVERY = 500;
// Per-worker spacing — Commons unauthenticated reads tolerate a few
// requests per second per IP but throttle aggressively (HTTP 429) when
// you burst. ~3 workers × 200ms = 15 req/s sustained, with backoff
// already wired into fetchCategoryFiles.
const WORKER_SLEEP_MS = 200;

interface CacheEntry {
  qid: string;
  image?: string;
  rangeMaps?: string[];
  commonsCat?: string;
  iucnStatus?: string;
  fetchedAt: string;
}

interface CategoryMember {
  ns: number;
  title: string;
}

// Image extensions Commons hosts that can be range maps.
const MAP_EXTENSIONS = /\.(svg|png|jpe?g|tiff?|gif)$/i;
// Things that look like media but aren't maps.
const SKIP_EXTENSIONS = /\.(ogg|ogv|oga|mp3|mp4|webm|pdf|djvu|wav|flac|stl)$/i;

// Strong keyword signals (any language we've seen). Word boundaries with
// punctuation/underscore. Sourced from the actual filename word frequency
// dump of existing rangeMaps[] entries, plus a few common European
// translations.
const KEYWORD_RE = new RegExp(
  [
    "\\bmap\\b",
    "\\brange\\b",
    "\\bdistribution\\b",
    "\\bdistmap\\b",
    "\\bdistr\\b",
    "\\bdist\\b",
    "\\bmapa\\b", // Spanish / Portuguese / Polish
    "\\bcarte\\b", // French
    "\\brépartition\\b", // French
    "\\brepartition\\b", // French (de-accented)
    "\\bdistribuzione\\b", // Italian
    "\\bverbreitung\\b", // German
    "\\bverbreiding\\b", // Dutch
    "\\bareal\\b", // Russian (transliteration)
    "\\bпоширення\\b", // Ukrainian
    "\\bкарта\\b", // Russian
    "\\bмапа\\b", // Ukrainian
    "\\brozmieszczenie\\b", // Polish
    "\\bzasięg\\b", // Polish
    "\\butbredelse\\b", // Norwegian / Swedish
    "\\biucn\\d*\\b", // e.g. "IUCN2019-2.png"
  ].join("|"),
  "iu",
);

// Negative keywords — file names that contain "map" but aren't range maps.
const ANTI_RE = /\b(roadmap|heatmap|sitemap|mapping|biomap|treemap|stylemap)\b/iu;

// Reject MediaWiki template-syntax leakage (`{{maplink}}`, `<mapframe …>`,
// `{{Location map …}}`) — these come back from the Commons API for pages
// that embed inline geo widgets instead of real files.
const TEMPLATE_SYNTAX_RE = /^[{<]|^File:.*[{<]/;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function loadCache(): Record<string, CacheEntry> {
  if (!existsSync(CACHE_PATH)) return {};
  return JSON.parse(readFileSync(CACHE_PATH, "utf-8")) as Record<string, CacheEntry>;
}

function saveCache(cache: Record<string, CacheEntry>) {
  mkdirSync(dirname(CACHE_PATH), { recursive: true });
  writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2) + "\n");
}

async function pushProgress(pct: number, msg: string, done = false) {
  try {
    await fetch(`${PROGRESSD_URL}/api/sessions/${SESSION_ID}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pct, message: msg, done, label: SESSION_LABEL }),
    });
  } catch {
    /* progressd optional */
  }
}

/** One API call → list of file titles in a Commons category. */
async function fetchCategoryFiles(cat: string): Promise<string[] | null> {
  // cmtitle wants "Category:Foo" — accept either form coming in.
  const cmtitle = cat.startsWith("Category:") ? cat : `Category:${cat}`;
  const params = new URLSearchParams({
    action: "query",
    list: "categorymembers",
    cmtitle,
    cmtype: "file",
    cmlimit: "200",
    format: "json",
    formatversion: "2",
  });

  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(`${API_URL}?${params.toString()}`, {
        headers: { "User-Agent": USER_AGENT, Accept: "application/json" },
        signal: AbortSignal.timeout(30_000),
      });
      if (res.status === 429) {
        const ra = parseInt(res.headers.get("retry-after") || "0", 10);
        await sleep((ra > 0 ? ra : 2 ** (attempt + 1)) * 1000);
        continue;
      }
      if (!res.ok) {
        await sleep(2 ** attempt * 1000);
        continue;
      }
      const json = (await res.json()) as {
        query?: { categorymembers?: CategoryMember[] };
      };
      const members = json.query?.categorymembers ?? [];
      return members
        .map((m) => m.title)
        .filter((t) => t.startsWith("File:"))
        .map((t) => t.slice("File:".length));
    } catch {
      await sleep(2 ** attempt * 1000);
    }
  }
  return null;
}

/** Filter file list down to plausible range-map files. */
function pickRangeMaps(files: string[], _binomial: string): string[] {
  // The cat itself is species-scoped (it's the species' own Commons cat),
  // so any image whose filename mentions a map/distribution/range keyword
  // is almost certainly the species' range map. We rely on the keyword
  // signal and skip the binomial-only branch — too noisy in testing
  // (matches photos labelled "Genus species map area X").
  const out: string[] = [];
  for (const raw of files) {
    if (TEMPLATE_SYNTAX_RE.test(raw)) continue;
    if (SKIP_EXTENSIONS.test(raw)) continue;
    if (!MAP_EXTENSIONS.test(raw)) continue;
    if (ANTI_RE.test(raw)) continue;
    if (!KEYWORD_RE.test(raw)) continue;
    out.push(raw);
  }
  // Prefer SVG first, then PNG, then others; preserve discovery order
  // inside each tier.
  const tier = (f: string) =>
    /\.svg$/i.test(f) ? 0 : /\.png$/i.test(f) ? 1 : 2;
  out.sort((a, b) => tier(a) - tier(b));
  return out;
}

interface MineStats {
  scanned: number;
  withResults: number;
  totalMaps: number;
  apiFailures: number;
}

async function processOne(
  binomial: string,
  entry: CacheEntry,
  stats: MineStats,
): Promise<void> {
  const cat = entry.commonsCat;
  if (!cat) return;
  const files = await fetchCategoryFiles(cat);
  stats.scanned++;
  if (files === null) {
    stats.apiFailures++;
    return;
  }
  const maps = pickRangeMaps(files, binomial);
  if (maps.length === 0) return;
  const existing = new Set(entry.rangeMaps ?? []);
  const added = maps.filter((m) => !existing.has(m));
  if (added.length === 0) return;
  entry.rangeMaps = [...(entry.rangeMaps ?? []), ...added];
  stats.withResults++;
  stats.totalMaps += added.length;
  if (process.env.SN_MINER_DEBUG) {
    console.log(`  + ${binomial}: ${added.join(", ")}`);
  }
}

async function main() {
  const args = process.argv.slice(2);
  const limitIdx = args.indexOf("--limit");
  const limit = limitIdx >= 0 ? parseInt(args[limitIdx + 1] ?? "0", 10) : 0;
  const concIdx = args.indexOf("--concurrency");
  const concurrency =
    concIdx >= 0
      ? Math.max(1, parseInt(args[concIdx + 1] ?? "0", 10))
      : DEFAULT_CONCURRENCY;
  const dry = args.includes("--dry-run");

  console.log(`Loading ${CACHE_PATH}…`);
  const cache = loadCache();
  const allKeys = Object.keys(cache);
  console.log(`  ${allKeys.length.toLocaleString()} cache entries`);

  // Queue: have commonsCat, no rangeMaps yet.
  const queue: string[] = [];
  for (const k of allKeys) {
    const e = cache[k];
    if (!e.commonsCat) continue;
    if (e.rangeMaps && e.rangeMaps.length > 0) continue;
    queue.push(k);
  }
  console.log(`  queue: ${queue.length.toLocaleString()} entries with commonsCat but no rangeMap`);

  if (limit > 0 && queue.length > limit) {
    queue.length = limit;
    console.log(`  --limit ${limit}: trimmed`);
  }
  if (queue.length === 0) {
    await pushProgress(100, "Nothing to do", true);
    return;
  }

  await pushProgress(0, `Starting: ${queue.length} cats to mine`);

  const stats: MineStats = {
    scanned: 0,
    withResults: 0,
    totalMaps: 0,
    apiFailures: 0,
  };
  const t0 = Date.now();
  let savePending = 0;

  // Run a sliding window of `concurrency` workers.
  let cursor = 0;
  const total = queue.length;

  async function worker() {
    while (true) {
      const i = cursor++;
      if (i >= total) return;
      const binomial = queue[i];
      const entry = cache[binomial];
      await processOne(binomial, entry, stats);
      savePending++;
      // Periodic save + progress update from the worker that crosses
      // SAVE_EVERY. Cheap; saveCache is fast at this file size.
      if (savePending >= SAVE_EVERY) {
        savePending = 0;
        if (!dry) saveCache(cache);
        const elapsed = (Date.now() - t0) / 1000;
        const rate = stats.scanned / elapsed;
        const eta = Math.round((total - stats.scanned) / Math.max(rate, 0.01));
        const pct = (stats.scanned / total) * 100;
        const msg = `${stats.scanned.toLocaleString()}/${total.toLocaleString()} · hits=${stats.withResults} maps=${stats.totalMaps} · ${rate.toFixed(1)}/s · ETA ${Math.floor(eta / 60)}m${eta % 60}s`;
        console.log(`  ${pct.toFixed(1)}% ${msg}`);
        await pushProgress(pct, msg);
      }
      await sleep(WORKER_SLEEP_MS);
    }
  }

  await Promise.all(Array.from({ length: concurrency }, () => worker()));

  if (!dry) saveCache(cache);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
  const summary = `Done in ${elapsed}s · scanned ${stats.scanned} · ${stats.withResults} hits · ${stats.totalMaps} new range maps · ${stats.apiFailures} api failures`;
  console.log(summary);
  await pushProgress(100, summary, true);
}

main().catch(async (e) => {
  console.error("Fatal:", e);
  await pushProgress(0, `Fatal: ${(e as Error).message}`, true);
  process.exit(1);
});
