#!/usr/bin/env node
/**
 * importPlantVascularFromWcvp.ts
 *
 * Reads portal/data/wcvp-cache.json and imports species into the 38
 * exact-match empty vascular plant families (conifers, cycads, ferns,
 * lycophytes, gnetophytes, ginkgo).
 *
 * For each matched family, creates:
 *   <class>/<order>/<family>/src/data/<family>.json
 * with genus-grouped species, stamped sourcedFrom="powo".
 *
 * Usage:
 *   npx tsx scripts/importPlantVascularFromWcvp.ts
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE_PATH = resolve(root, "portal", "data", "wcvp-cache.json");
const TAX_PATH = resolve(root, "portal", "data", "taxonomy-plantae-snippet.json");

interface WcvpSpecies {
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
  acceptedByFamily: Record<string, WcvpSpecies[]>;
}

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

function buildDescription(sp: WcvpSpecies, className: string): string {
  const parts: string[] = [];
  if (sp.taxonRemarks) {
    parts.push(`The native range of this species is ${sp.taxonRemarks}.`);
  }
  const lfOk = sp.lifeform && sp.lifeform.toLowerCase() !== "unknown";
  const clOk = sp.climate && sp.climate.toLowerCase() !== "unknown";
  if (lfOk && clOk) {
    parts.push(`It is a ${sp.lifeform} and grows primarily in the ${sp.climate} biome.`);
  } else if (lfOk) {
    parts.push(`It is a ${sp.lifeform}.`);
  } else if (clOk) {
    parts.push(`It grows primarily in the ${sp.climate} biome.`);
  }
  if (!parts.length) {
    parts.push(`${sp.binomial} — a ${className.toLowerCase()} species in the genus ${sp.genus}.`);
  }
  return parts.join(" ");
}

function main() {
  console.log("📦 Loading WCVP cache...");
  const cache: WcvpCache = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));

  console.log("📂 Loading plant taxonomy...");
  const tax = JSON.parse(readFileSync(TAX_PATH, "utf-8"));

  const tracheoClasses = new Set([
    "Pinopsida", "Cycadopsida", "Ginkgoopsida", "Lycopodiopsida",
    "Gnetopsida", "Polypodiopsida",
  ]);

  interface Target {
    className: string;
    orderName: string;
    familyName: string;
    appSlug: string;
    species: WcvpSpecies[];
  }

  const targets: Target[] = [];
  const wcvpFams = cache.acceptedByFamily;
  const normalized = new Map(Object.keys(wcvpFams).map(k => [k.toLowerCase(), k]));

  let currentClass = "";
  let currentOrder = "";
  function walk(n: any) {
    if (n.rank === "CLASS") {
      currentClass = tracheoClasses.has(n.name) ? n.name : "";
      if (!currentClass) currentOrder = "";
    }
    if (n.rank === "ORDER" && currentClass) {
      currentOrder = n.name;
    }
    if (n.rank === "FAMILY" && currentClass && n.appSlug) {
      const wcvpKey = normalized.get(n.appSlug);
      if (wcvpKey) {
        const species = wcvpFams[wcvpKey];
        if (species && species.length > 0) {
          targets.push({
            className: currentClass,
            orderName: currentOrder,
            familyName: n.name,
            appSlug: n.appSlug,
            species,
          });
        }
      }
      return;
    }
    for (const c of n.children ?? []) {
      walk(c);
    }
  }
  for (const c of tax.children ?? []) {
    walk(c);
  }

  console.log(`\n🎯 ${targets.length} families to import (${targets.reduce((s, t) => s + t.species.length, 0)} total species)\n`);

  let created = 0;
  let skipped = 0;

  for (const t of targets) {
    const slug = t.appSlug;
    const classDir = t.className.toLowerCase();
    const orderDir = t.orderName.toLowerCase();
    const dataDir = resolve(root, classDir, orderDir, slug, "src", "data");
    const dataPath = resolve(dataDir, `${slug}.json`);

    process.stdout.write(`  ${t.className}/${t.orderName}/${t.familyName} (${t.species.length} spp) … `);

    if (existsSync(dataPath)) {
      const existing = JSON.parse(readFileSync(dataPath, "utf-8"));
      if ((existing.children?.length ?? 0) > 0 || (existing.speciesList?.length ?? 0) > 0) {
        console.log(`⏭️  skipped (exists)`);
        skipped++;
        continue;
      }
    }

    // Group by genus
    const genusMap = new Map<string, WcvpSpecies[]>();
    for (const sp of t.species) {
      const genus = sp.genus || sp.binomial.split(" ")[0] || "Unknown";
      if (!genusMap.has(genus)) genusMap.set(genus, []);
      genusMap.get(genus)!.push(sp);
    }

    const children: any[] = [];
    for (const [genusName, spp] of genusMap) {
      const speciesChildren = spp.map(sp => ({
        id: nameToId(sp.binomial),
        name: sp.binomial,
        rank: "SPECIES",
        commonName: sp.binomial,
        lineage: genusName,
        subspeciesCount: 0,
        description: buildDescription(sp, t.className),
        sourcedFrom: "powo",
      }));
      speciesChildren.sort((a, b) => a.name.localeCompare(b.name));
      children.push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of ${t.className.toLowerCase()}s.`,
        lineage: genusName,
        children: speciesChildren,
      });
    }

    mkdirSync(dataDir, { recursive: true });
    writeFileSync(dataPath, JSON.stringify({
      id: makeId(slug, "FAM"),
      name: t.familyName,
      rank: "FAMILY",
      commonName: t.familyName,
      children,
    }, null, 2) + "\n");

    console.log(`✅ ${children.length} genera, ${t.species.length} spp`);
    created++;
  }

  console.log(`\n✅ Done! ${created} created, ${skipped} skipped`);
}

main();
