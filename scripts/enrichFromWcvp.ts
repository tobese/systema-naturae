#!/usr/bin/env node
/**
 * enrichFromWcvp.ts
 *
 * Reads portal/data/wcvp-cache.json and enriches existing species in
 * data files (*.json) under plant class directories.  For each non-
 * Wikipedia species with a minimal or no description, builds a richer
 * description from WCVP fields (native range, lifeform, climate).
 *
 * Wikipedia-sourced species are left untouched.
 *
 * Usage:
 *   npx tsx scripts/enrichFromWcvp.ts
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "fs";
import { resolve, dirname, join, sep } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE_PATHS = [
  "/Volumes/MacieExternal/tmp/opencode/wcvp-cache.json",
  resolve(root, "portal", "data", "wcvp-cache.json"),
];

interface WcvpEntry {
  ipniId: string;
  binomial: string;
  genus: string;
  species: string;
  authors: string;
  taxonRemarks: string | null;
  lifeform: string | null;
  climate: string | null;
}

interface WcvpCache {
  version: string;
  downloadedAt: string;
  acceptedByFamily: Record<string, WcvpEntry[]>;
}

interface TaxonNode {
  id?: string;
  name?: string;
  rank?: string;
  commonName?: string;
  description?: string;
  sourcedFrom?: string;
  subspeciesCount?: number;
  lineage?: string;
  children?: TaxonNode[];
  speciesList?: TaxonNode[];
  [key: string]: unknown;
}

/** Extract the clean binomial (genus + species) from a node name that may include author, hybrid markers, etc. */
function extractBinomial(name: string): string {
  const parts = name.trim().split(/\s+/);
  // Keep first two non-empty parts, strip leading "×" from first
  const genus = parts[0]?.replace(/^[×x]\s*/, "") || "";
  const species = parts[1] || "";
  return `${genus} ${species}`.toLowerCase();
}

function buildDescription(entry: WcvpEntry, className: string): string {
  const parts: string[] = [];
  if (entry.taxonRemarks) {
    parts.push(`The native range of this species is ${entry.taxonRemarks}.`);
  }
  const lfOk = entry.lifeform && entry.lifeform.toLowerCase() !== "unknown";
  const clOk = entry.climate && entry.climate.toLowerCase() !== "unknown";
  if (lfOk && clOk) {
    parts.push(`It is a ${entry.lifeform} and grows primarily in the ${entry.climate} biome.`);
  } else if (lfOk) {
    parts.push(`It is a ${entry.lifeform}.`);
  } else if (clOk) {
    parts.push(`It grows primarily in the ${entry.climate} biome.`);
  }
  return parts.join(" ");
}

function isMinimalDescription(desc: string | undefined): boolean {
  if (!desc || desc.length < 40) return true;
  return /a \w+ species in the genus/i.test(desc);
}

const MINIMAL_SOURCES = new Set(["none", "generated", "", undefined]);

// Walks taxonomy/plantae/ rather than a list of class directories. The list
// was hard-coded and each entry existedSync-guarded, which fails in the worst
// direction: under taxonomy/<kingdom>/<phylum>/<class>/ none of those paths
// exist, so the loop skipped every one of them and the script went on to
// report success having enriched nothing. The per-file path indexing below
// had already been updated for the new layout, which is why this looked fixed.
const KINGDOM_ROOT = resolve(root, "taxonomy", "plantae");

/** Find all family data JSON files under a directory tree. */
function findDataFiles(baseDir: string): string[] {
  const results: string[] = [];
  function walk(dir: string) {
    let entries: string[];
    try { entries = readdirSync(dir); } catch { return; }
    for (const e of entries) {
      const full = join(dir, e);
      try {
        const s = statSync(full);
        if (s.isDirectory()) {
          walk(full);
        } else if (e.endsWith(".json") && full.includes(join("src", "data"))) {
          results.push(full);
        }
      } catch { /* skip unreadable */ }
    }
  }
  walk(baseDir);
  return results;
}

function main() {
  process.stdout.write("Loading WCVP cache... ");
  const cachePath = CACHE_PATHS.find(p => existsSync(p));
  if (!cachePath) {
    console.error("\n❌ WCVP cache not found. Run scripts/cacheWcvp.py first.");
    process.exit(1);
  }
  const cache: WcvpCache = JSON.parse(readFileSync(cachePath, "utf-8"));
  const wcvp = cache.acceptedByFamily;
  console.log(`${Object.keys(wcvp).length} families, ${Object.values(wcvp).reduce((s, v) => s + v.length, 0)} species`);

  // Build normalized map: family_lower → original key
  const famLookup = new Map<string, string>();
  for (const key of Object.keys(wcvp)) {
    famLookup.set(key.toLowerCase(), key);
  }

  // Build family+binomial → WCVP entry
  const binomialLookup = new Map<string, { wcvpKey: string; entry: WcvpEntry }>();
  for (const [famKey, entries] of Object.entries(wcvp)) {
    const famLower = famKey.toLowerCase();
    for (const entry of entries) {
      const bKey = `${famLower}::${entry.binomial.toLowerCase()}`;
      binomialLookup.set(bKey, { wcvpKey: famKey, entry });
    }
  }

  let enrichedCount = 0;
  let skippedWikipedia = 0;
  let skippedAlready = 0;
  let noMatch = 0;
  let enrichedFamilies = 0;
  let noDataFamilies = 0;

  if (!existsSync(KINGDOM_ROOT)) {
    console.error(`No ${KINGDOM_ROOT} - nothing to enrich. Refusing to report success.`);
    process.exit(1);
  }
  const kingdomDirs = readdirSync(KINGDOM_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => join(KINGDOM_ROOT, d.name));
  if (!kingdomDirs.length) {
    console.error(`${KINGDOM_ROOT} has no subdirectories. Refusing to report success.`);
    process.exit(1);
  }

  for (const kingdomDir of kingdomDirs) {
    const files = findDataFiles(kingdomDir);
    for (const filePath of files) {
      const relPath = filePath.replace(root + sep, "");
      const data: TaxonNode = JSON.parse(readFileSync(filePath, "utf-8"));

      // taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json
      // Indexes from the end. parts[2] used to be the family under the old
      // class/order/family layout; after the move it is the class, so appSlug
      // silently became a class name and the script wrote under the wrong key.
      const parts = relPath.split(sep);
      const appSlug = parts[parts.length - 4];
      const className = parts[parts.length - 6];

      // Check if WCVP has this family
      if (!famLookup.has(appSlug)) {
        noDataFamilies++;
        continue;
      }

      let familyChanged = false;

      function enrichNode(node: TaxonNode) {
        if (!node) return;

        if (node.rank !== "SPECIES") {
          for (const c of node.children ?? []) enrichNode(c);
          for (const s of node.speciesList ?? []) enrichNode(s);
          return;
        }

        const name = node.name || "";
        const sourcedFrom = node.sourcedFrom || "";

        // Skip Wikipedia-sourced species
        if (sourcedFrom === "wikipedia") {
          skippedWikipedia++;
          return;
        }

        // Skip if already has a good non-minimal description
        if (!MINIMAL_SOURCES.has(sourcedFrom) && !isMinimalDescription(node.description)) {
          skippedAlready++;
          return;
        }

        // Extract binomial and look up
        const binomial = extractBinomial(name);
        const lookupKey = `${appSlug}::${binomial}`;
        const match = binomialLookup.get(lookupKey);
        if (!match) {
          noMatch++;
          return;
        }

        const newDesc = buildDescription(match.entry, className);
        if (!newDesc) return;

        node.description = newDesc;
        if (MINIMAL_SOURCES.has(sourcedFrom)) {
          node.sourcedFrom = "powo";
        }
        enrichedCount++;
        familyChanged = true;
      }

      enrichNode(data);

      if (familyChanged) {
        writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
        enrichedFamilies++;
      }
    }
  }

  console.log(`\nDone.`);
  console.log(`  Families enriched:     ${enrichedFamilies}`);
  console.log(`  Species descriptions:  ${enrichedCount}`);
  console.log(`  Wikipedia skipped:     ${skippedWikipedia}`);
  console.log(`  Already good:          ${skippedAlready}`);
  console.log(`  No WCVP match:         ${noMatch}`);
  console.log(`  Families w/o WCVP:     ${noDataFamilies}`);
}

main();
