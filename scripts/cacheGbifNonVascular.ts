#!/usr/bin/env node
/**
 * cacheGbifNonVascular.ts
 *
 * Downloads accepted species for every EMPTY non-vascular plant family
 * (bryophytes + algae) from the GBIF backbone, mirroring how
 * cacheWcvp.py built the vascular cache. Families are resolved by name
 * against the GBIF backbone, then their species are paginated via
 * higherTaxonKey (the proper taxonomic filter).
 *
 * Output: /Volumes/MacieExternal/tmp/opencode/gbif-cache-nonvascular.json
 *   (with a local fallback portal/data/gbif-cache-nonvascular.json)
 *
 * Resume-safe: already-cached families are skipped on re-run.
 *
 * Usage:
 *   npx tsx scripts/cacheGbifNonVascular.ts
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const TAX_PATH = resolve(root, "portal", "data", "taxonomy-plantae-snippet.json");
const OUT_PATHS = [
  "/Volumes/MacieExternal/tmp/opencode/gbif-cache-nonvascular.json",
  resolve(root, "portal", "data", "gbif-cache-nonvascular.json"),
];

const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const BACKBONE = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c";
const RATE_MS = 250;
const MAX_RETRIES = 5;

const VASCULAR_CLASSES = new Set([
  "Magnoliopsida", "Liliopsida", "Pinopsida", "Cycadopsida",
  "Ginkgoopsida", "Gnetopsida", "Polypodiopsida", "Lycopodiopsida", "Equisetopsida",
]);

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

interface SpeciesRecord {
  scientificName: string;
  canonicalName: string;
  genus: string;
  species: string;
  family: string;
}

interface FamilyCache {
  family: string;
  appSlug: string;
  gbifKey: number;
  speciesCount: number;
  species: SpeciesRecord[];
}

interface GbifNonVascularCache {
  version: string;
  downloadedAt: string;
  speciesByFamily: Record<string, FamilyCache>;
}

async function fetchWithRetry(url: string, retries = MAX_RETRIES): Promise<any> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeout);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e: any) {
      if (attempt < retries) {
        const wait = Math.min(1000 * Math.pow(2, attempt), 15000);
        process.stderr.write(`  retry ${attempt}/${retries} in ${wait}ms: ${e.message}\n`);
        await sleep(wait);
        continue;
      }
      throw e;
    }
  }
}

async function paginate(urlBase: string): Promise<any[]> {
  const out: any[] = [];
  let offset = 0;
  const limit = 200;
  while (true) {
    const url = `${urlBase}&limit=${limit}&offset=${offset}`;
    const data = await fetchWithRetry(url);
    const results = data.results ?? [];
    out.push(...results);
    if (results.length < limit) break;
    offset += limit;
    await sleep(RATE_MS);
  }
  return out;
}

async function resolveFamilyKey(familyName: string): Promise<number | null> {
  const url = `${GBIF_SEARCH}?q=${encodeURIComponent(familyName)}&rank=FAMILY&datasetKey=${BACKBONE}&limit=10`;
  const data = await fetchWithRetry(url);
  const results = data.results ?? [];
  // Prefer an ACCEPTED family with this exact name
  for (const r of results) {
    if (r.rank === "FAMILY" && (r.canonicalName || "").toLowerCase() === familyName.toLowerCase()) {
      if (r.status === "ACCEPTED" || r.status === null) return r.nubKey ?? r.key;
    }
  }
  for (const r of results) {
    if (r.rank === "FAMILY" && (r.canonicalName || "").toLowerCase() === familyName.toLowerCase()) {
      return r.nubKey ?? r.key;
    }
  }
  return null;
}

function collectEmptyFamilies(): { className: string; orderName: string; familyName: string; appSlug: string }[] {
  const tax = JSON.parse(readFileSync(TAX_PATH, "utf-8"));
  const out: any[] = [];
  function walk(n: any, cls = "", order = "") {
    if (n.rank === "CLASS") cls = n.name;
    if (n.rank === "ORDER") order = n.name;
    if (n.rank === "FAMILY" && n.appSlug) {
      if (VASCULAR_CLASSES.has(cls)) return;
      const p = resolve(root, cls.toLowerCase(), order.toLowerCase(), n.appSlug, "src", "data", `${n.appSlug}.json`);
      if (!existsSync(p)) {
        out.push({ className: cls, orderName: order, familyName: n.name, appSlug: n.appSlug });
      }
    }
    for (const c of n.children ?? []) walk(c, cls, order);
  }
  walk(tax);
  return out;
}

async function main() {
  const targets = collectEmptyFamilies();
  console.log(`📋 ${targets.length} empty non-vascular families to cache`);

  // Load or init cache
  let cache: GbifNonVascularCache;
  const existing = OUT_PATHS.map((p) => (existsSync(p) ? p : null)).find(Boolean);
  if (existing) {
    cache = JSON.parse(readFileSync(existing, "utf-8"));
    console.log(`♻️  Resuming from ${existing} (${Object.keys(cache.speciesByFamily).length} families cached)`);
  } else {
    cache = {
      version: "gbif-nonvascular/1",
      downloadedAt: new Date().toISOString(),
      speciesByFamily: {},
    };
  }

  let done = 0;
  let failed = 0;

  for (const t of targets) {
    if (cache.speciesByFamily[t.appSlug]) {
      done++;
      continue;
    }

    process.stdout.write(`  ${t.familyName} … `);
    let gbifKey: number | null = null;
    try {
      gbifKey = await resolveFamilyKey(t.familyName);
    } catch (e: any) {
      process.stdout.write(`key-error\n`);
      failed++;
      await sleep(RATE_MS);
      continue;
    }
    if (!gbifKey) {
      process.stdout.write(`not in GBIF\n`);
      // Record empty so we don't retry forever
      cache.speciesByFamily[t.appSlug] = {
        family: t.familyName, appSlug: t.appSlug, gbifKey: 0, speciesCount: 0, species: [],
      };
      done++;
      await sleep(RATE_MS);
      continue;
    }

    try {
      const recs = await paginate(
        `${GBIF_SEARCH}?higherTaxonKey=${gbifKey}&rank=SPECIES&status=ACCEPTED&datasetKey=${BACKBONE}`,
      );
      const species: SpeciesRecord[] = recs
        .filter((r) => r.rank === "SPECIES")
        .map((r) => ({
          scientificName: r.scientificName || r.canonicalName,
          canonicalName: r.canonicalName,
          genus: r.genus || (r.canonicalName ? r.canonicalName.split(" ")[0] : ""),
          species: r.species || (r.canonicalName ? r.canonicalName.split(" ")[1] || "" : ""),
          family: r.family || t.familyName,
        }));
      cache.speciesByFamily[t.appSlug] = {
        family: t.familyName, appSlug: t.appSlug, gbifKey,
        speciesCount: species.length, species,
      };
      process.stdout.write(`${species.length} spp ✅\n`);
      done++;
    } catch (e: any) {
      process.stdout.write(`species-error\n`);
      failed++;
    }

    // Persist incrementally
    const json = JSON.stringify(cache, null, 2);
    for (const p of OUT_PATHS) {
      try {
        mkdirSync(require("path").dirname(p), { recursive: true });
        writeFileSync(p, json);
      } catch { /* try next path */ }
    }
    await sleep(RATE_MS);
  }

  console.log(`\n✅ Done. ${done} families processed, ${failed} failed.`);
  const totalSpp = Object.values(cache.speciesByFamily).reduce((s, f) => s + f.speciesCount, 0);
  console.log(`   Total species cached: ${totalSpp.toLocaleString()}`);
}

main();
