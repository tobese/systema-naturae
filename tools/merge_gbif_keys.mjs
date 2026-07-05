#!/usr/bin/env node
/**
 * merge_gbif_keys.mjs — fold the flat gbif-keys-{class}.json usageKey maps into
 * the structured gbif-cache-{class}.json files as a top-level `usageKeys` field,
 * and also stamp `usageKey` onto matching per-species records.
 *
 * After a successful merge the temp gbif-keys-{class}.json files can be removed.
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const DATA = resolve(root, "portal", "data");
const CLASSES = ["liliopsida", "magnoliopsida"];

for (const cls of CLASSES) {
  const keysPath = resolve(DATA, `gbif-keys-${cls}.json`);
  const cachePath = resolve(DATA, `gbif-cache-${cls}.json`);

  if (!existsSync(keysPath)) { console.log(`[${cls}] no keys file, skip`); continue; }
  if (!existsSync(cachePath)) { console.log(`[${cls}] no cache file, skip`); continue; }

  const keys = JSON.parse(readFileSync(keysPath, "utf-8"));
  const cache = JSON.parse(readFileSync(cachePath, "utf-8"));

  const keyCount = Object.keys(keys).length;
  const withKey = Object.values(keys).filter(v => v !== null).length;

  // 1. Attach the flat map at top level
  cache.usageKeys = keys;

  // 2. Stamp usageKey onto each species record where the canonicalName matches
  let stamped = 0, unmatched = 0;
  for (const fam of Object.values(cache.speciesByFamily ?? {})) {
    for (const sp of fam.species ?? []) {
      const binom = (sp.canonicalName || sp.species || "").split(/\s+/).slice(0, 2).join(" ");
      if (binom && binom in keys) {
        if (keys[binom] !== null) { sp.usageKey = keys[binom]; stamped++; }
      } else {
        unmatched++;
      }
    }
  }

  cache.usageKeysMergedAt = new Date().toISOString();
  writeFileSync(cachePath, JSON.stringify(cache, null, 2) + "\n");

  console.log(`[${cls}] merged ${keyCount} keys (${withKey} resolved) → ${cachePath.split("/").pop()}`);
  console.log(`[${cls}]   stamped usageKey on ${stamped} species records (${unmatched} cache species had no flat-map entry)`);
}

console.log("\nDone. Verify, then remove tools' temp gbif-keys-*.json files if desired.");
