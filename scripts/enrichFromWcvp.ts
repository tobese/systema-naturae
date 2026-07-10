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

const CACHE_PATH = resolve(root, "portal", "data", "wcvp-cache.json");

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

const CLASS_DIRS = [
  "magnoliopsida", "liliopsida",
  "pinopsida", "cycadopsida", "ginkgoopsida",
  "gnetopsida", "polypodiopsida", "lycopodiopsida",
];

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
  const cache: WcvpCache = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));
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

  for (const classDir of CLASS_DIRS) {
    const fullDir = resolve(root, classDir);
    if (!existsSync(fullDir)) continue;

    const files = findDataFiles(fullDir);
    for (const filePath of files) {
      const relPath = filePath.replace(root + sep, "");
      const data: TaxonNode = JSON.parse(readFileSync(filePath, "utf-8"));

      // Extract appSlug from path: e.g. magnoliopsida/lamiales/acanthaceae/src/data/acanthaceae.json
      const parts = relPath.split(sep);
      const appSlug = parts[2];
      const className = parts[0];

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
