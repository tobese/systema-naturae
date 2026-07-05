#!/usr/bin/env node
/**
 * cache_gbif_keys.mjs — Walk all plant JSON trees, fetch GBIF usageKeys,
 * and cache them in portal/data/gbif-keys-{class}.json.
 *
 * Run one or more instances (each with --id N --total M to shard):
 *   node tools/cache_gbif_keys.mjs
 *   node tools/cache_gbif_keys.mjs --id 0 --total 4   # shard 0 of 4
 *   node tools/cache_gbif_keys.mjs --id 1 --total 4   # shard 1 of 4 (parallel)
 *
 * Rate-limited to ~5 req/s across all instances.
 */
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "fs";
import { resolve, dirname, join, sep } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; usage-key cache)";
const CACHE_PATH = (cls) => resolve(root, "portal", "data", `gbif-keys-${cls}.json`);
const CLASSES = ["liliopsida", "magnoliopsida"];

const RPS = 20;
const SAVE_EVERY = 5000;

const args = process.argv.slice(2);
const arg = (f, d) => { const i = args.indexOf(f); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const SHARD_ID = Number(arg("--id", "0"));
const SHARD_TOTAL = Number(arg("--total", "1"));

function loadCache(cls) {
  const p = CACHE_PATH(cls);
  if (!existsSync(p)) return {};
  try { return JSON.parse(readFileSync(p, "utf-8")); } catch { return {}; }
}

function saveCache(cls, cache) {
  writeFileSync(CACHE_PATH(cls), JSON.stringify(cache, null, 2) + "\n");
}

function binomial(n) {
  return n.split(/\s+/).slice(0, 2).join(" ");
}

async function gbifMatch(name) {
  const url = `${GBIF_MATCH}?name=${encodeURIComponent(name)}&strict=true`;
  const res = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(15000) });
  if (!res.ok) return null;
  const data = await res.json();
  return data.usageKey || data.canonicalUsageKey || null;
}

let tock = Date.now();
async function rateLimit() {
  const now = Date.now();
  const elapsed = now - tock;
  const minGap = 1000 / RPS;
  if (elapsed < minGap) await new Promise(r => setTimeout(r, minGap - elapsed));
  tock = Date.now();
}

async function main() {
  const files = [];
  for (const cls of CLASSES) {
    const d = resolve(root, cls);
    if (!existsSync(d)) continue;
    (function walk(p) {
      let es; try { es = readdirSync(p); } catch { return; }
      for (const n of es) {
        const fp = join(p, n);
        let st; try { st = statSync(fp); } catch { continue; }
        if (st.isDirectory()) walk(fp);
        else if (fp.endsWith(".json") && fp.includes(`${sep}src${sep}data${sep}`)) files.push(fp);
      }
    })(d);
  }
  files.sort();

  // Shard
  const myFiles = files.filter((_, i) => i % SHARD_TOTAL === SHARD_ID);
  console.log(`[${SHARD_ID}/${SHARD_TOTAL}] ${myFiles.length} files (of ${files.length})`);

  let totalSpecies = 0;
  let cached = 0;
  let matched = 0;
  let missed = 0;
  let saved = 0;

  // Pre-collect all species names
  const allSpecies = []; // { cls, name }
  for (const fp of myFiles) {
    let tree; try { tree = JSON.parse(readFileSync(fp, "utf-8")); } catch { continue; }
    const cls = fp.includes(`${sep}liliopsida${sep}`) ? "liliopsida" : "magnoliopsida";
    (function walk(node) {
      if (node.rank === "SPECIES") {
        const b = binomial(node.name ?? "");
        if (b) allSpecies.push({ cls, binom: b, name: node.name });
        return;
      }
      for (const c of node.children ?? []) walk(c);
    })(tree);
  }

  console.log(`[${SHARD_ID}/${SHARD_TOTAL}] ${allSpecies.length} species to process`);

  // Load existing caches
  const caches = {};
  for (const cls of CLASSES) caches[cls] = loadCache(cls);

  // Process with concurrency
  const CONCURRENCY = 5;
  let idx = 0;

  const workers = Array.from({ length: CONCURRENCY }, async () => {
    for (;;) {
      const i = idx++;
      if (i >= allSpecies.length) break;
      const { cls, binom } = allSpecies[i];

      if (binom in caches[cls]) {
        cached++;
        continue;
      }

      await rateLimit();
      const key = await gbifMatch(binom).catch(() => null);
      caches[cls][binom] = key; // null means "not found in GBIF"
      if (key !== null) matched++;
      else missed++;

      totalSpecies++;

      if (totalSpecies % SAVE_EVERY === 0) {
        for (const c of CLASSES) saveCache(c, caches[c]);
        saved++;
        const pct = ((i + 1) / allSpecies.length * 100).toFixed(1);
        console.log(`[${SHARD_ID}/${SHARD_TOTAL}] ${i + 1}/${allSpecies.length} (${pct}%) — cached:${cached} matched:${matched} missed:${missed}`);
      }
    }
  });

  await Promise.all(workers);

  // Final save
  for (const c of CLASSES) saveCache(c, caches[c]);
  console.log(`\n[${SHARD_ID}/${SHARD_TOTAL}] DONE — cached:${cached} matched:${matched} missed:${missed} (${allSpecies.length} total)`);
}

main().catch(e => { console.error(e); process.exit(1); });
