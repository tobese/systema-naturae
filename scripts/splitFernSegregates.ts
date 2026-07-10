#!/usr/bin/env node
/**
 * splitFernSegregates.ts
 *
 * WCVP treats the polypod ferns under a broad Polypodiaceae s.l. Our
 * taxonomy uses the narrower PPG I families (Dryopteridaceae,
 * Tectariaceae, Lomariopsidaceae, ...). This splits the genera currently
 * lumped in polypodiopsida/polypodiales/polypodiaceae/ into their correct
 * segregate families, creating a data file for each target family that
 * exists in the taxonomy and leaving the core Polypodiaceae s.s. genera
 * behind.
 *
 * Usage:
 *   npx tsx scripts/splitFernSegregates.ts
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

// Genus -> segregate family (PPG I). Genera absent here stay in Polypodiaceae s.s.
const GENUS_TO_FAMILY: Record<string, string> = {
  Arachniodes: "Dryopteridaceae",
  Ctenitis: "Dryopteridaceae",
  Cyclodium: "Dryopteridaceae",
  Cyclopeltis: "Dryopteridaceae",
  Cyrtomium: "Dryopteridaceae",
  Dryopolystichum: "Dryopteridaceae",
  Dryopteris: "Dryopteridaceae",
  Dryostichum: "Dryopteridaceae",
  Hypoderris: "Dryopteridaceae",
  Lastreopsis: "Dryopteridaceae",
  Maxonia: "Dryopteridaceae",
  Megalastrum: "Dryopteridaceae",
  Mickelia: "Dryopteridaceae",
  Olfersia: "Dryopteridaceae",
  Parapolystichum: "Dryopteridaceae",
  Phanerophlebia: "Dryopteridaceae",
  Polybotrya: "Dryopteridaceae",
  Polystichopsis: "Dryopteridaceae",
  Polystichum: "Dryopteridaceae",
  Pteridrys: "Dryopteridaceae",
  Rumohra: "Dryopteridaceae",
  Stigmatopteris: "Dryopteridaceae",
  Trichoneuron: "Dryopteridaceae",
  Bosmania: "Dryopteridaceae",
  Cyclobotrya: "Dryopteridaceae",

  Tectaria: "Tectariaceae",
  Arthropteris: "Tectariaceae",
  Pleocnemia: "Tectariaceae",
  Triplophyllum: "Tectariaceae",
  Draconopteris: "Tectariaceae",

  Elaphoglossum: "Lomariopsidaceae",
  Lomariopsis: "Lomariopsidaceae",
  Lomagramma: "Lomariopsidaceae",
  Teratophyllum: "Lomariopsidaceae",
  Thylacopteris: "Lomariopsidaceae",
  Dracoglossum: "Lomariopsidaceae",

  Davallia: "Davalliaceae",
  Didymochlaena: "Didymochlaenaceae",
  Nephrolepis: "Nephrolepidaceae",
  Oleandra: "Oleandraceae",
};

function famId(slug: string): string {
  return `FAM_${slug.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function main() {
  const polyPath = resolve(root, "polypodiopsida", "polypodiales", "polypodiaceae", "src", "data", "polypodiaceae.json");
  const poly = JSON.parse(readFileSync(polyPath, "utf-8"));
  const genera: any[] = poly.children ?? [];

  const buckets: Record<string, any[]> = {};
  const remaining: any[] = [];

  for (const g of genera) {
    const fam = GENUS_TO_FAMILY[g.name];
    if (fam) {
      (buckets[fam] ||= []).push(g);
    } else {
      remaining.push(g);
    }
  }

  let created = 0;
  let moved = 0;

  for (const [famName, famGenera] of Object.entries(buckets)) {
    const slug = famName.toLowerCase();
    const famDir = resolve(root, "polypodiopsida", "polypodiales", slug);
    const dataDir = resolve(famDir, "src", "data");
    const dataPath = resolve(dataDir, `${slug}.json`);

    if (existsSync(dataPath)) {
      console.log(`⏭  ${famName} already exists — skipping`);
      continue;
    }

    mkdirSync(dataDir, { recursive: true });
    const file = {
      id: famId(slug),
      name: famName,
      rank: "FAMILY",
      commonName: famName,
      children: famGenera,
    };
    writeFileSync(dataPath, JSON.stringify(file, null, 2) + "\n");
    created++;
    const spp = famGenera.reduce((s, g) => s + (g.children?.length ?? 0), 0);
    moved += famGenera.length;
    console.log(`✅ ${famName}: ${famGenera.length} genera, ${spp} spp`);
  }

  // Rewrite Polypodiaceae with remaining (core) genera
  poly.children = remaining;
  writeFileSync(polyPath, JSON.stringify(poly, null, 2) + "\n");
  const remSpp = remaining.reduce((s, g) => s + (g.children?.length ?? 0), 0);
  console.log(`\n📝 Polypodiaceae s.s. kept: ${remaining.length} genera, ${remSpp} spp`);
  console.log(`Created ${created} segregate family files, moved ${moved} genera.`);
}

main();
