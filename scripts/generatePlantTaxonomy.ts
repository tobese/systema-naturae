/**
 * Generate Plantae taxonomy.json entries, color themes, species-news events.
 *
 * Usage: npx tsx scripts/generatePlantTaxonomy.ts
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const portalRoot = resolve(root, "portal");

interface ScoutEntry {
  name: string;
  rank: string;
  gbifKey: number;
  speciesCount: number;
  children?: ScoutEntry[];
}

interface CacheData {
  speciesByFamily: Record<string, { species: any[] }>;
}

const PLANT_PHYLA: { name: string; commonName: string; scoutFile: string; caches: string[] }[] = [
  { name: "Tracheophyta", commonName: "Vascular plants", scoutFile: "gbif-scout-tracheophyta.json", caches: ["gbif-cache-liliopsida.json", "gbif-cache-magnoliopsida.json"] },
  { name: "Bryophyta", commonName: "Mosses", scoutFile: "gbif-scout-bryophyta.json", caches: [] },
  { name: "Marchantiophyta", commonName: "Liverworts", scoutFile: "gbif-scout-marchantiophyta.json", caches: [] },
  { name: "Anthocerotophyta", commonName: "Hornworts", scoutFile: "gbif-scout-anthocerotophyta.json", caches: [] },
  { name: "Chlorophyta", commonName: "Green algae", scoutFile: "gbif-scout-chlorophyta.json", caches: [] },
  { name: "Rhodophyta", commonName: "Red algae", scoutFile: "gbif-scout-rhodophyta.json", caches: [] },
  { name: "Charophyta", commonName: "Stoneworts", scoutFile: "gbif-scout-charophyta.json", caches: [] },
];

function loadScout(filename: string): ScoutEntry | null {
  const p = resolve(portalRoot, "data", filename);
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf-8")) : null;
}

function loadCache(filename: string): CacheData | null {
  const p = resolve(portalRoot, "data", filename);
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf-8")) : null;
}

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function slugify(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function generateColor(index: number, total: number) {
  const hue = ((index * 137.508 + 30) % 360).toString();
  const hue2 = ((index * 137.508 + 30 + 30) % 360).toString();
  return {
    accent: `hsl(${hue}, 55%, 40%)`,
    bg: `hsl(${hue}, 25%, 92%)`,
    bgAlt: `hsl(${hue}, 20%, 96%)`,
    border: `hsl(${hue}, 30%, 70%)`,
    familyTree: `hsl(${hue2}, 40%, 50%)`,
    nodeFill: `hsl(${hue}, 35%, 70%)`,
    nodeStroke: `hsl(${hue}, 50%, 35%)`,
  };
}

function main() {
  const allFamilies: { slug: string; name: string }[] = [];
  const today = new Date().toISOString().split("T")[0];

  // Pre-scan: collect all family slugs across all phyla with caches
  const cachesByClass: Map<string, CacheData> = new Map();
  for (const phylum of PLANT_PHYLA) {
    for (const cacheFile of phylum.caches) {
      const cache = loadCache(cacheFile);
      if (cache) {
        const clsName = cacheFile
          .replace("gbif-cache-", "").replace(".json", "")
          .split("-").map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(" ");
        cachesByClass.set(clsName, cache);
      }
    }
  }

  // First pass: collect families for indexing (deterministic order)
  for (const phylum of PLANT_PHYLA) {
    const scout = loadScout(phylum.scoutFile);
    if (!scout) continue;
    for (const cls of scout.children ?? []) {
      if (cls.rank !== "CLASS") continue;
      for (const ord of cls.children ?? []) {
        if (ord.rank !== "ORDER") continue;
        for (const fam of ord.children ?? []) {
          if (fam.rank !== "FAMILY") continue;
          const slug = slugify(fam.name);
          if (!allFamilies.find(f => f.slug === slug)) allFamilies.push({ slug, name: fam.name });
        }
      }
    }
  }

  // Build the taxonomy tree
  const output: any = {
    id: "PLANTAE",
    name: "Plantae",
    rank: "KINGDOM",
    commonName: "Plants",
    description: "Plantae is one of the major kingdoms of life, encompassing multicellular, photosynthetic eukaryotes. Plants range from tiny mosses to giant trees and are fundamental to Earth's ecosystems as primary producers.",
    children: [],
  };

  const colorLines: string[] = [];
  const newsEntries: any[] = [];

  for (const phylum of PLANT_PHYLA) {
    const scout = loadScout(phylum.scoutFile);
    if (!scout) continue;

    const phylumChildren: any[] = [];

    for (const cls of scout.children ?? []) {
      if (cls.rank !== "CLASS") continue;
      const cache = cachesByClass.get(cls.name);
      const speciesByFamily = cache?.speciesByFamily ?? {};

      const classChildren: any[] = [];

      for (const ord of cls.children ?? []) {
        if (ord.rank !== "ORDER") continue;
        const orderChildren: any[] = [];

        for (const fam of ord.children ?? []) {
          if (fam.rank !== "FAMILY") continue;
          const slug = slugify(fam.name);
          if (orderChildren.find((f: any) => f.appSlug === slug)) continue;

          const spCount = speciesByFamily[fam.name]
            ? speciesByFamily[fam.name].species.length
            : fam.speciesCount ?? 0;

          orderChildren.push({
            id: makeId(slug, "FAM"),
            name: fam.name,
            rank: "FAMILY",
            commonName: fam.name,
            appSlug: slug,
            speciesCount: spCount,
            notableMembers: [],
          });

          // Color theme
          const idx = allFamilies.findIndex(f => f.slug === slug);
          if (idx >= 0) {
            const theme = generateColor(idx, allFamilies.length);
            const constName = `${slug.replace(/-/g, "_").toUpperCase()}_THEME`;
            colorLines.push(`const ${constName}: ColorTheme = ${JSON.stringify(theme)};`);
            colorLines.push(`colorRegistry.set("${slug}", ${constName});`);
          }

          // News event
          newsEntries.push({ type: "family_added", family: slug, name: fam.name, date: today });
        }

        if (orderChildren.length > 0) {
          classChildren.push({
            id: makeId(ord.name, "ORD"),
            name: ord.name,
            rank: "ORDER",
            commonName: ord.name,
            children: orderChildren,
          });
        }
      }

      if (classChildren.length > 0) {
        phylumChildren.push({
          id: makeId(cls.name, "CLS"),
          name: cls.name,
          rank: "CLASS",
          commonName: cls.name,
          children: classChildren,
        });
      }
    }

    if (phylumChildren.length > 0) {
      output.children.push({
        id: makeId(phylum.name, "PHY"),
        name: phylum.name,
        rank: "PHYLUM",
        commonName: phylum.commonName,
        children: phylumChildren,
      });
    }
  }

  // Write outputs
  writeFileSync(resolve(portalRoot, "data", "taxonomy-plantae-snippet.json"), JSON.stringify(output, null, 2) + "\n");
  writeFileSync(resolve(portalRoot, "data", "color-registry-plantae.txt"), colorLines.join("\n") + "\n");
  writeFileSync(resolve(portalRoot, "data", "species-news-plantae.json"), JSON.stringify(newsEntries, null, 2) + "\n");

  // Summary
  let totalFamilies = 0, totalSpp = 0;
  for (const phylum of output.children) {
    for (const cls of phylum.children ?? []) {
      for (const ord of cls.children ?? []) {
        for (const fam of ord.children ?? []) {
          totalFamilies++;
          totalSpp += fam.speciesCount;
        }
      }
    }
  }
  console.log(`Phyla with data: ${output.children.map((p: any) => p.name).join(", ")}`);
  console.log(`Families: ${totalFamilies}, Species: ~${totalSpp.toLocaleString()}`);
  console.log(`Color themes: ${allFamilies.length}, News events: ${newsEntries.length}`);
  console.log(`\nOutput files:
  portal/data/taxonomy-plantae-snippet.json
  portal/data/color-registry-plantae.txt
  portal/data/species-news-plantae.json`);
}

main();
