/**
 * enrichHigherRanks.ts
 *
 * Enrich PHYLUM / CLASS / ORDER node `description` (and `commonName` when
 * missing) from REAL sources only — never generated text.
 *
 *   Source ladder per node:
 *     1. Wikipedia REST summary  (/api/rest_v1/page/summary/{title})
 *        title resolution: exact scientific name -> redirect (automatic)
 *        -> Wikipedia search fallback -> try commonName.
 *     2. EOL pages API           (descriptive text objects)
 *
 *   Only `description` + `sourcedFrom` are written. We deliberately do NOT
 *   auto-fill `commonName`: Wikipedia's short `description` field is a
 *   classification phrase ("Order of fishes", "Phylum of marine animals"),
 *   not a vernacular name, so writing it would corrupt that field. Human-
 *   curated commonNames are left untouched.
 *
 *   GBIF is intentionally NOT used for prose: its `/descriptions` are messy
 *   literature snippets. (Our taxonomy already carries the hierarchy GBIF
 *   would only confirm.) Unresolvable nodes are left untouched and recorded
 *   in the gap report — no synthetic fallback.
 *
 * Usage:
 *   npx tsx scripts/enrichHigherRanks.ts [kingdom] [--write] [--limit N] [--dry]
 *   kingdom defaults to $SN_KINGDOM or "animalia".
 *   Default is a DRY RUN (network lookups, no file write). Pass --write to persist.
 */

import { readFileSync, writeFileSync, existsSync, copyFileSync } from "fs";
import { resolve, join } from "path";

// Resolve the portal root by walking up from cwd until we find
// data/kingdom-config.json. Robust to how the script is invoked (tsx
// does not expose a usable import.meta.url in this environment).
function findPortalRoot(): string {
  let dir = process.cwd();
  for (;;) {
    if (existsSync(join(dir, "data", "kingdom-config.json"))) return dir;
    const parent = resolve(dir, "..");
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

const portalRoot = findPortalRoot();
const configPath = resolve(portalRoot, "data/kingdom-config.json");
const gapReportPath = (kingdom: string) =>
  resolve(portalRoot, `data/description-gap-report-${kingdom}.json`);

const RANKS = ["PHYLUM", "CLASS", "ORDER"] as const;
type Rank = (typeof RANKS)[number];

const DELAY_MS = 1200;
const UA = "SystemaNaturae/1.0 (taxonomy enrichment; contact: local)";
const DESC_MIN = 20; // node considered "missing description" if shorter than this
const DESC_CAP = 400; // max chars written to description

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Wikipedia (and EOL) rate-limit aggressively (~10 rapid hits → HTTP 429).
// Retry with backoff, honouring Retry-After; transient failures are NOT cached
// upstream, so a later re-run can retry them.
async function fetchWithRetry(url: string, opts: any = {}, retries = 3, baseDelay = 1500): Promise<any> {
  let lastErr: any;
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, { ...opts, signal: AbortSignal.timeout(15000) });
      if (res.status === 429) {
        const ra = res.headers.get("retry-after");
        const delay = ra ? parseInt(ra, 10) * 1000 : baseDelay * (i + 1);
        await sleep(delay);
        continue;
      }
      if (res.status >= 500 && res.status < 600) {
        await sleep(baseDelay * (i + 1));
        continue;
      }
      return res;
    } catch (e) {
      lastErr = e;
      await sleep(baseDelay * (i + 1));
    }
  }
  throw lastErr ?? new Error("fetchWithRetry exhausted");
}

// ── arg parsing ─────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const KINGDOM = argv.find((a) => !a.startsWith("--")) ?? process.env.SN_KINGDOM ?? "animalia";
const WRITE = argv.includes("--write");
const limitArg = argv.find((a) => a.startsWith("--limit="));
const li = argv.findIndex((a) => a === "--limit" || a.startsWith("--limit="));
let LIMIT = Infinity;
if (li !== -1) {
  const raw = argv[li].startsWith("--limit=") ? argv[li].split("=")[1] : argv[li + 1];
  if (raw) LIMIT = parseInt(raw, 10);
}

// ── caches (avoid refetching the same title) ────────────────────────────────
const summaryCache = new Map<string, { extract?: string; description?: string } | null>();
const searchCache = new Map<string, string | null>();
const eolCache = new Map<string, string | null>();

// ── Wikipedia REST summary ───────────────────────────────────────────────────
async function wikiSummary(title: string): Promise<{ extract?: string; description?: string } | null> {
  if (summaryCache.has(title)) return summaryCache.get(title)!;
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`;
  try {
    const res = await fetchWithRetry(url, { headers: { "User-Agent": UA } });
    if (res.status === 404) {
      summaryCache.set(title, null);
      return null;
    }
    const d = (await res.json()) as any;
    if (d.extract && d.extract.length >= DESC_MIN && !/may refer to/i.test(d.extract)) {
      const r = { extract: d.extract, description: d.description };
      summaryCache.set(title, r);
      return r;
    }
    summaryCache.set(title, null); // empty or disambiguation → permanent miss
    return null;
  } catch {
    return null; // transient (429/network) after retries → NOT cached, retryable
  }
}

async function wikiSearch(title: string): Promise<string | null> {
  if (searchCache.has(title)) return searchCache.get(title)!;
  const url =
    `https://en.wikipedia.org/w/api.php?action=query&list=search` +
    `&srsearch=${encodeURIComponent(title)}&format=json&srlimit=4&origin=*`;
  let found: string | null = null;
  try {
    const res = await fetchWithRetry(url, { headers: { "User-Agent": UA } });
    if (res.ok) {
      const d = (await res.json()) as any;
      const results: any[] = d?.query?.search ?? [];
      // Prefer an exact title match.
      const exact = results.find((r) => r.title.toLowerCase() === title.toLowerCase());
      if (exact) found = exact.title;
      else {
        const top = results[0]?.title;
        // Reject obvious non-article hits.
        if (top && !/^(list of|category:|template:|help:|wikipedia:)/i.test(top)) found = top;
      }
    }
  } catch {
    /* transient after retries → not cached */
  }
  searchCache.set(title, found);
  return found;
}

// ── EOL (Encyclopedia of Life) ───────────────────────────────────────────────
async function eolDescription(title: string): Promise<string | null> {
  if (eolCache.has(title)) return eolCache.get(title)!;
  let result: string | null = null;
  try {
    const sUrl = `https://eol.org/api/search/1.0.json?q=${encodeURIComponent(title)}&page=1`;
    const sRes = await fetchWithRetry(sUrl, { headers: { "User-Agent": UA } });
    if (sRes.ok) {
      const s = (await sRes.json()) as any;
      const id = s?.results?.[0]?.id;
      if (id) {
        const pUrl = `https://eol.org/api/pages/1.0/${id}.json?details=true&common_names=false`;
        const pRes = await fetchWithRetry(pUrl, { headers: { "User-Agent": UA } });
        if (pRes.ok) {
          const p = (await pRes.json()) as any;
          const objs: any[] = p?.data_objects ?? [];
          // Prefer an English, trusted descriptive text object.
          const pick =
            objs.find((o) => o.description && /^en/i.test(o.language ?? "") && /trusted/i.test(o.source ?? "")) ??
            objs.find((o) => o.description && /^en/i.test(o.language ?? "")) ??
            objs.find((o) => o.description);
          if (pick?.description && pick.description.length >= DESC_MIN) {
            result = pick.description.replace(/\s+/g, " ").trim();
          }
        }
      }
    }
  } catch {
    /* ignore */
  }
  eolCache.set(title, result);
  return result;
}

function trimDesc(s: string): string {
  const clean = s.replace(/\s+/g, " ").trim();
  if (clean.length <= DESC_CAP) return clean;
  const cut = clean.slice(0, DESC_CAP);
  const lastStop = Math.max(cut.lastIndexOf("."), cut.lastIndexOf("!"), cut.lastIndexOf("?"));
  return (lastStop > DESC_MIN ? cut.slice(0, lastStop + 1) : cut).trim();
}

interface Resolution {
  description?: string;
  commonName?: string;
  source?: "wikipedia" | "eol" | "wikidata";
}

async function resolveNode(node: any): Promise<Resolution | null> {
  const names = [node.name, node.commonName].filter(Boolean) as string[];

  // 1+2. Wikipedia (direct, then search, then commonName)
  for (const name of names) {
    let s = await wikiSummary(name);
    if (!s) {
      const found = await wikiSearch(name);
      if (found && found.toLowerCase() !== name.toLowerCase()) s = await wikiSummary(found);
    }
    if (s?.extract) {
      return { description: trimDesc(s.extract), source: "wikipedia" };
    }
  }

  // 3. EOL (descriptive text objects)
  for (const name of names) {
    const e = await eolDescription(name);
    if (e) return { description: trimDesc(e), source: "eol" };
  }

  return null;
}

// ── main ──────────────────────────────────────────────────────────────────────
function main() {
  if (!existsSync(configPath)) {
    console.error("kingdom-config.json not found at", configPath);
    process.exit(1);
  }
  const config = JSON.parse(readFileSync(configPath, "utf-8"));
  const kc = config.kingdoms?.[KINGDOM];
  if (!kc) {
    console.error(`Kingdom "${KINGDOM}" not in kingdom-config.json. Available:`, Object.keys(config.kingdoms));
    process.exit(1);
  }
  const inputRel = kc.input as string;
  const inputPath = resolve(portalRoot, inputRel);
  if (!existsSync(inputPath)) {
    console.error("Taxonomy input not found:", inputPath);
    process.exit(1);
  }

  const root = JSON.parse(readFileSync(inputPath, "utf-8"));
  const missing: any[] = [];
  (function walk(n: any) {
    if ((RANKS as readonly string[]).includes(n.rank)) {
      const d = n.description?.trim() ?? "";
      if (d.length <= DESC_MIN) missing.push(n);
    }
    for (const c of n.children ?? []) walk(c);
  })(root);

  console.log(`Kingdom: ${KINGDOM}`);
  console.log(`Taxonomy: ${inputRel}`);
  console.log(`Nodes missing description (<=${DESC_MIN} chars): ${missing.length}`);
  console.log(`Mode: ${WRITE ? "WRITE (persist)" : "DRY RUN (no write)"}`);
  console.log("");

  const tally = { wikipedia: 0, eol: 0, failed: 0 };
  const unresolvable: string[] = [];
  let processed = 0;

  (async () => {
    for (const node of missing) {
      if (processed >= LIMIT) break;
      processed++;
      const res = await resolveNode(node);
      if (res?.description) {
        if (WRITE) {
          node.description = res.description;
          if (res.source) node.sourcedFrom = res.source;
        }
        tally[res.source as "wikipedia" | "eol"]++;
        const tag = res.source?.toUpperCase().padEnd(8);
        console.log(`  [${tag}] ${node.rank.padEnd(7)} ${node.name}`);
      } else {
        tally.failed++;
        unresolvable.push(`${node.rank}:${node.name}`);
        console.log(`  [MISS]     ${node.rank.padEnd(7)} ${node.name}`);
      }
      if (processed < missing.length) await sleep(DELAY_MS + Math.random() * 600);
    }

    if (WRITE) {
      const bak = inputPath + ".bak";
      if (!existsSync(bak)) copyFileSync(inputPath, bak);
      writeFileSync(inputPath, JSON.stringify(root, null, 2) + "\n");
      writeGapReport(KINGDOM, missing, tally, unresolvable);
      console.log(`\nWrote ${inputPath} (backup: ${bak})`);
    }

    console.log("\n────────────────────────────────────────");
    console.log(`Processed:     ${processed}`);
    console.log(`  Wikipedia:   ${tally.wikipedia}`);
    console.log(`  EOL:         ${tally.eol}`);
    console.log(`  Unresolvable:${tally.failed}`);
    console.log(WRITE ? "Persisted: YES" : "Persisted: NO (dry run)");
  })();
}

// ── gap report ────────────────────────────────────────────────────────────────
function writeGapReport(kingdom: string, missing: any[], tally: any, unresolvable: string[]) {
  const path = gapReportPath(kingdom);
  let report: any = {};
  if (existsSync(path)) {
    try {
      report = JSON.parse(readFileSync(path, "utf-8"));
    } catch {
      report = {};
    }
  }
  const enriched = tally.wikipedia + tally.eol + tally.wikidata;

  // Per-rank totals come from a fresh walk of the (now updated) missing list.
  const perRank: Record<string, { missing: number; enrichedNow: number }> = {};
  for (const r of RANKS) perRank[r] = { missing: 0, enrichedNow: 0 };

  report.kingdoms = report.kingdoms ?? {};
  report.kingdoms[kingdom] = {
    generatedAt: new Date().toISOString(),
    enrichedThisRun: enriched,
    unresolvableIds: unresolvable,
    note: "Higher-rank (PHYLUM/CLASS/ORDER) description coverage. Run enrichHigherRanks.ts per kingdom.",
  };
  report.totalEnrichedThisRun = (report.totalEnrichedThisRun ?? 0) + enriched;
  writeFileSync(path, JSON.stringify(report, null, 2) + "\n");
}

main();
