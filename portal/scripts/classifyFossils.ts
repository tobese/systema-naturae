/**
 * classifyFossils.ts
 *
 * Classify PHYLUM / CLASS / ORDER nodes as `extinct` and/or `fossil` from REAL
 * sources only — never generated text. "Total recall": every higher-rank node
 * is attempted (not just keyword candidates).
 *
 *   Source ladder per node:
 *     1. Wikipedia REST summary  (/api/rest_v1/page/summary/{title})
 *        → use the short `description` phrase ("extinct order of molluscs") as
 *        the PRECISE signal, and the `extract` as a prose fallback.
 *     2. Wikipedia search fallback → try resolved title.
 *
 *   Two distinct schema fields are populated (per shared/src/types.ts):
 *     - `extinct`: recorded in human history, no longer exists (e.g. Dodo).
 *     - `fossil` : known only from the fossil record, never observed alive
 *                  (e.g. trilobites). At higher ranks an extinct clade is, by
 *                  definition, known only from fossils, so extinct ⇒ fossil.
 *
 *   Only `extinct`/`fossil` booleans are written onto the SOURCE higher-rank
 *   node. buildData.ts already spreads node fields through for higher ranks,
 *   so they flow into unified-taxonomy.json unchanged.
 *
 * Usage:
 *   npx tsx scripts/classifyFossils.ts [kingdom] [--write] [--limit N]
 *   kingdom defaults to $SN_KINGDOM or "animalia".
 *   Default is a DRY RUN (network lookups, no file write). Pass --write to persist.
 */

import { readFileSync, writeFileSync, existsSync, copyFileSync, renameSync } from "fs";
import { resolve, join } from "path";

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
  resolve(portalRoot, `data/fossil-gap-report-${kingdom}.json`);

const RANKS = ["PHYLUM", "CLASS", "ORDER"] as const;

const DELAY_MS = 1200;
const UA = "SystemaNaturae/1.0 (fossil classification; contact: local)";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Wikipedia rate-limits aggressively (~10 rapid hits → HTTP 429). Retry with
// backoff, honouring Retry-After; transient failures are NOT cached upstream.
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
const li = argv.findIndex((a) => a === "--limit" || a.startsWith("--limit="));
let LIMIT = Infinity;
if (li !== -1) {
  const raw = argv[li].startsWith("--limit=") ? argv[li].split("=")[1] : argv[li + 1];
  if (raw) LIMIT = parseInt(raw, 10);
}

// ── caches ───────────────────────────────────────────────────────────────────
const summaryCache = new Map<string, { extract?: string; description?: string } | null>();
const searchCache = new Map<string, string | null>();

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
    // Accept even short extracts here — we only need the phrase + prose signal.
    if (d.extract && !/may refer to/i.test(d.extract)) {
      const r = { extract: d.extract, description: d.description };
      summaryCache.set(title, r);
      return r;
    }
    summaryCache.set(title, null);
    return null;
  } catch {
    return null;
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
      const exact = results.find((r) => r.title.toLowerCase() === title.toLowerCase());
      if (exact) found = exact.title;
      else {
        const top = results[0]?.title;
        if (top && !/^(list of|category:|template:|help:|wikipedia:)/i.test(top)) found = top;
      }
    }
  } catch {
    /* transient → not cached */
  }
  searchCache.set(title, found);
  return found;
}

// ── conservative classifier ───────────────────────────────────────────────────
// Primary signal: the precise Wikipedia summary phrase (+ † prefix). A guard rejects
// "extinct relatives/ancestors" so Aves etc. are not flagged.
// Secondary: STRICT patterns on the portal node.description — only direct assertions
// ("extinct order of …", "known only from fossils") — so extant groups that merely
// mention fossils ("earliest fossil loons…") are NOT false-positived.
// Returns { extinct, fossil, src }.
function classify(name: string, phrase: string | undefined, desc: string | undefined) {
  if (name.startsWith("†")) return { extinct: true, fossil: true, src: "dagger-prefix" };
  const p = (phrase || "").toLowerCase();
  const d = (desc || "").toLowerCase();

  const hasExtinct = /\bextinct\b/.test(p);
  const hasFossil =
    /\b(fossil|prehistoric) (genus|order|family|class|phylum|clade|group|subfamily|tribe|superorder|subclass)\b/.test(p) ||
    /^an? (fossil|prehistoric)\b/.test(p) ||
    /\bprehistoric\b/.test(p) ||
    /\b(known|recorded|represented) (only|solely|entirely) from fossils?\b/.test(p);
  const relativeGuard =
    /extinct (relatives?|cousins?|members?|ancestors?)/.test(p) ||
    /(living|extant)[^.]{0,25}extinct/.test(p);

  // Reject bare "fossil" in "fossil record / fossil specimens / fossil evidence"
  // (extant groups have those too) — only a classifying "fossil X" adjective counts.
  const fossilRecordGuard = /\bfossil (record|records|specimen|specimens|evidence|calibrat)/.test(p);
  if ((hasExtinct && !relativeGuard) || (hasFossil && !fossilRecordGuard)) {
    return { extinct: true, fossil: true, src: "wiki-description" };
  }

  const descExtinct =
    /\bextinct (order|class|family|phylum|clade|group|subclass|superorder|subfamily) of\b/.test(d) ||
    /\b(known|recorded|represented) (only|solely|entirely) from fossils?\b/.test(d);
  const descFossil = /\b(known|recorded|represented) (only|solely|entirely) from fossils?\b/.test(d);
  if (descExtinct || descFossil) {
    return { extinct: true, fossil: true, src: "description" };
  }
  return { extinct: false, fossil: false, src: "none" };
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
  const targets: any[] = [];
  (function walk(n: any) {
    if ((RANKS as readonly string[]).includes(n.rank)) targets.push(n);
    for (const c of n.children ?? []) walk(c);
  })(root);

  console.log(`Kingdom: ${KINGDOM}`);
  console.log(`Taxonomy: ${inputRel}`);
  console.log(`Higher-rank nodes (PHYLUM/CLASS/ORDER): ${targets.length}`);
  console.log(`Mode: ${WRITE ? "WRITE (persist)" : "DRY RUN (no write)"}`);
  console.log("");

  const tally = { classified: 0, fossil: 0, extinct: 0, none: 0, skipped: 0 };
  const classified: any[] = [];
  const none: any[] = [];
  let processed = 0;

  function flush() {
    if (!WRITE) return;
    const bak = inputPath + ".bak";
    if (!existsSync(bak)) copyFileSync(inputPath, bak);
    // Atomic: write to .tmp then rename, so a crash mid-write can never leave a
    // half-written/corrupted source file (the original stays intact on failure).
    const tmp = inputPath + ".tmp";
    writeFileSync(tmp, JSON.stringify(root, null, 2) + "\n");
    renameSync(tmp, inputPath);
    writeGapReport(KINGDOM, tally, classified, none);
  }

  (async () => {
    try {
      for (const node of targets) {
        if (processed >= LIMIT) break;
        processed++;

        // Resume: skip nodes already confirmed non-fossil (explicit false/false) AND
        // whose text mentions no fossil/extinct clue — no re-fetch. Nodes still flagged
        // true/undefined, OR false but textually mentioning fossils, are re-evaluated
        // (corrects false positives and catches obscure fossil orders).
        const mentionsFossil = /\bextinct\b|\bfossil\b/i.test((node.name || "") + (node.description || ""));
        if (node.extinct === false && node.fossil === false && !mentionsFossil) {
          tally.skipped++;
          tally.none++;
          none.push({ rank: node.rank, name: node.name });
          continue;
        }

        try {
          const names = [node.name, node.commonName].filter(Boolean) as string[];
          let phrase: string | undefined, extract: string | undefined;
          for (const nm of names) {
            let s = await wikiSummary(nm);
            if (!s) {
              const found = await wikiSearch(nm);
              if (found && found.toLowerCase() !== nm.toLowerCase()) s = await wikiSummary(found);
            }
            if (s) {
              phrase = s.description;
              extract = s.extract;
              break;
            }
          }

          const { extinct, fossil, src } = classify(node.name, phrase, node.description);
          if (extinct || fossil) {
            if (WRITE) {
              if (extinct) node.extinct = true;
              if (fossil) node.fossil = true;
            }
            tally.classified++;
            if (fossil) tally.fossil++;
            if (extinct) tally.extinct++;
            classified.push({ rank: node.rank, name: node.name, fossil, extinct, src, phrase: phrase ?? null });
            console.log(`  [${src.toUpperCase().padEnd(14)}] ${node.rank.padEnd(7)} ${node.name}  fossil=${fossil} extinct=${extinct}`);
          } else {
            tally.none++;
            none.push({ rank: node.rank, name: node.name });
            if (WRITE) { node.extinct = false; node.fossil = false; }
            if (node.name !== "Unknown") console.log(`  [NONE]     ${node.rank.padEnd(7)} ${node.name}`);
          }
        } catch (err) {
          const msg = (err as Error).message;
          console.error(`  [ERROR]    ${node.rank.padEnd(7)} ${node.name}: ${msg}`);
          if (WRITE) { node.extinct = false; node.fossil = false; }
          tally.none++;
          none.push({ rank: node.rank, name: node.name, error: msg });
        }
        if (processed < targets.length) await sleep(DELAY_MS + Math.random() * 600);
      }
    } catch (fatal) {
      console.error("FATAL loop error:", (fatal as Error).message);
    }

    flush();

    console.log("\n────────────────────────────────────────");
    console.log(`Processed:     ${processed}`);
    console.log(`  Classified:  ${tally.classified} (fossil=${tally.fossil}, extinct=${tally.extinct})`);
    console.log(`  None:        ${tally.none}`);
    console.log(`  Skipped:     ${tally.skipped}`);
    console.log(WRITE ? "Persisted: YES" : "Persisted: NO (dry run)");
  })();
}

// ── gap report ────────────────────────────────────────────────────────────────
function writeGapReport(kingdom: string, tally: any, classified: any[], none: any[]) {
  const path = gapReportPath(kingdom);
  const report = {
    kingdom,
    generatedAt: new Date().toISOString(),
    totals: {
      targets: tally.classified + tally.none,
      classified: tally.classified,
      fossil: tally.fossil,
      extinct: tally.extinct,
      none: tally.none,
    },
    classified,
    none,
  };
  writeFileSync(path, JSON.stringify(report, null, 2) + "\n");
}

main();
