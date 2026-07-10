#!/usr/bin/env node
/**
 * importNonVascularFromGbif.ts
 *
 * Reads portal/data/gbif-cache-nonvascular.json (built by
 * cacheGbifNonVascular.ts) and creates family data files for every
 * non-vascular family that has species. Species are grouped by genus
 * and stamped sourcedFrom="gbif".
 *
 * Usage:
 *   npx tsx scripts/importNonVascularFromGbif.ts
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE_PATHS = [
  "/Volumes/MacieExternal/tmp/opencode/gbif-cache-nonvascular.json",
  resolve(root, "portal", "data", "gbif-cache-nonvascular.json"),
];
const TAX_PATH = resolve(root, "portal", "data", "taxonomy-plantae-snippet.json");

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

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}
function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

function main() {
  const cachePath = CACHE_PATHS.find((p) => existsSync(p));
  if (!cachePath) {
    console.error("❌ Cache not found. Run scripts/cacheGbifNonVascular.ts first.");
    process.exit(1);
  }
  const cache: { speciesByFamily: Record<string, FamilyCache> } = JSON.parse(readFileSync(cachePath, "utf-8"));

  // Build appSlug -> {className, orderName}
  const tax = JSON.parse(readFileSync(TAX_PATH, "utf-8"));
  const slugMap = new Map<string, { className: string; orderName: string }>();
  function walk(n: any, cls = "", order = "") {
    if (n.rank === "CLASS") cls = n.name;
    if (n.rank === "ORDER") order = n.name;
    if (n.rank === "FAMILY" && n.appSlug) slugMap.set(n.appSlug, { className: cls, orderName: order });
    for (const c of n.children ?? []) walk(c, cls, order);
  }
  walk(tax);

  let created = 0;
  let skipped = 0;

  for (const fam of Object.values(cache.speciesByFamily)) {
    if (fam.speciesCount === 0) continue;
    const slug = fam.appSlug;
    const loc = slugMap.get(slug);
    if (!loc) {
      console.log(`⚠️  no taxonomy location for ${slug}`);
      continue;
    }
    const classDir = loc.className.toLowerCase();
    const orderDir = loc.orderName.toLowerCase();
    const dataDir = resolve(root, classDir, orderDir, slug, "src", "data");
    const dataPath = resolve(dataDir, `${slug}.json`);

    if (existsSync(dataPath)) {
      skipped++;
      continue;
    }

    // Group by genus
    const genusMap = new Map<string, SpeciesRecord[]>();
    for (const sp of fam.species) {
      const genus = sp.genus || sp.canonicalName.split(" ")[0] || "Unknown";
      if (!genusMap.has(genus)) genusMap.set(genus, []);
      genusMap.get(genus)!.push(sp);
    }

    const children: any[] = [];
    for (const [genusName, spp] of genusMap) {
      const speciesChildren = spp.map((sp) => ({
        id: nameToId(sp.canonicalName || sp.scientificName),
        name: sp.canonicalName || sp.scientificName,
        rank: "SPECIES",
        commonName: sp.canonicalName || sp.scientificName,
        lineage: genusName,
        subspeciesCount: 0,
        description: `${sp.canonicalName || sp.scientificName} — a ${loc.className.toLowerCase()} species in the genus ${genusName}.`,
        sourcedFrom: "gbif",
      }));
      speciesChildren.sort((a, b) => a.name.localeCompare(b.name));
      children.push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of ${loc.className.toLowerCase()}s.`,
        lineage: genusName,
        children: speciesChildren,
      });
    }

    mkdirSync(dataDir, { recursive: true });
    writeFileSync(dataPath, JSON.stringify({
      id: makeId(slug, "FAM"),
      name: fam.family,
      rank: "FAMILY",
      commonName: fam.family,
      children,
    }, null, 2) + "\n");

    created++;
    if (created % 25 === 0) console.log(`  created ${created} …`);
  }

  console.log(`\n✅ Done. ${created} family files created, ${skipped} skipped.`);
}

main();
