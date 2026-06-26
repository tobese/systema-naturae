import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");

const reportPath = join(root, "portal", "data", "gap-report.json");
if (!existsSync(reportPath)) {
  console.error(`Error: Gap report file not found at ${reportPath}`);
  process.exit(1);
}

const rawReport = readFileSync(reportPath, "utf-8");
const families = JSON.parse(rawReport);

// Map class names to Phyla
const CLASS_TO_PHYLUM: Record<string, { id: string; name: string; commonName: string; rank: number }> = {
  "Mammalia": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  "Aves": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  "Reptilia": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  "Amphibia": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  "Chondrichthyes": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  "Actinopterygii": { id: "CHORDATA", name: "Chordata", commonName: "Chordates", rank: 1 },
  
  "Cephalopoda": { id: "MOLLUSCA", name: "Mollusca", commonName: "Molluscs", rank: 2 },
  
  "Insecta": { id: "ARTHROPODA", name: "Arthropoda", commonName: "Arthropods", rank: 3 },
  "Arachnida": { id: "ARTHROPODA", name: "Arthropoda", commonName: "Arthropods", rank: 3 },
  
  "Asteroidea": { id: "ECHINODERMATA", name: "Echinodermata", commonName: "Echinoderms", rank: 4 },
  "Echinoidea": { id: "ECHINODERMATA", name: "Echinodermata", commonName: "Echinoderms", rank: 4 },
  "Holothuroidea": { id: "ECHINODERMATA", name: "Echinodermata", commonName: "Echinoderms", rank: 4 },
  
  // Empty class name is Tardigrada
  "": { id: "TARDIGRADA", name: "Tardigrada", commonName: "Tardigrades", rank: 5 },

  // Ctenophora
  "Tentaculata": { id: "CTENOPHORA", name: "Ctenophora", commonName: "Comb jellies", rank: 6 },
  "Nuda": { id: "CTENOPHORA", name: "Ctenophora", commonName: "Comb jellies", rank: 6 },

  // Cnidaria
  "Anthozoa": { id: "CNIDARIA", name: "Cnidaria", commonName: "Cnidarians", rank: 7 },
  "Hydrozoa": { id: "CNIDARIA", name: "Cnidaria", commonName: "Cnidarians", rank: 7 },
  "Scyphozoa": { id: "CNIDARIA", name: "Cnidaria", commonName: "Cnidarians", rank: 7 },
  "Cubozoa": { id: "CNIDARIA", name: "Cnidaria", commonName: "Cnidarians", rank: 7 },
  "Staurozoa": { id: "CNIDARIA", name: "Cnidaria", commonName: "Cnidarians", rank: 7 }
};

interface PhylumStats {
  id: string;
  name: string;
  commonName: string;
  rank: number;
  classes: Record<string, {
    name: string;
    families: any[];
    speciesCount: number;
    portalCount: number;
    minimalCount: number;
    enrichedCount: number;
  }>;
  speciesCount: number;
  portalCount: number;
  minimalCount: number;
  enrichedCount: number;
  totalGaps: number;
  hasGaps: boolean;
}

const phylaGroups: Record<string, PhylumStats> = {};

for (const f of families) {
  const className = f.className || "";
  const phylumInfo = CLASS_TO_PHYLUM[className] || { id: "OTHER", name: "Other", commonName: "Other Invertebrates", rank: 99 };
  const phylumId = phylumInfo.id;
  
  if (!phylaGroups[phylumId]) {
    phylaGroups[phylumId] = {
      id: phylumId,
      name: phylumInfo.name,
      commonName: phylumInfo.commonName,
      rank: phylumInfo.rank,
      classes: {},
      speciesCount: 0,
      portalCount: 0,
      minimalCount: 0,
      enrichedCount: 0,
      totalGaps: 0,
      hasGaps: false
    };
  }
  
  const pGroup = phylaGroups[phylumId];
  
  // Track class stats within phylum
  const classKey = className || "Tardigrada";
  if (!pGroup.classes[classKey]) {
    pGroup.classes[classKey] = {
      name: classKey,
      families: [],
      speciesCount: 0,
      portalCount: 0,
      minimalCount: 0,
      enrichedCount: 0
    };
  }
  
  const cGroup = pGroup.classes[classKey];
  cGroup.families.push(f);
  cGroup.speciesCount += f.speciesCount || 0;
  cGroup.portalCount += f.portalCount || 0;
  cGroup.minimalCount += f.minimalCount || 0;
  cGroup.enrichedCount += f.enrichedCount || 0;
  
  // Aggregate to phylum
  pGroup.speciesCount += f.speciesCount || 0;
  pGroup.portalCount += f.portalCount || 0;
  pGroup.minimalCount += f.minimalCount || 0;
  pGroup.enrichedCount += f.enrichedCount || 0;
  
  if (f.portalCount < f.speciesCount) {
    pGroup.hasGaps = true;
    pGroup.totalGaps += (f.speciesCount - f.portalCount);
  }
}

const sortedPhyla = Object.values(phylaGroups).sort((a, b) => a.rank - b.rank);

// 1. Console report
console.log();
console.log(`${"Phylum".padEnd(16)} ${"Common Name".padEnd(16)} ${"Classes".padEnd(8)} ${"Families".padEnd(8)} ${"Species Known".padEnd(14)} ${"Imported".padEnd(10)} ${"Enriched".padEnd(10)} ${"Gaps".padEnd(8)} ${"Complete %"}`);
console.log("=".repeat(105));

for (const p of sortedPhyla) {
  const classesCount = Object.keys(p.classes).length;
  const familiesCount = Object.values(p.classes).reduce((sum, c) => sum + c.families.length, 0);
  const completePct = p.speciesCount === 0 ? 100 : (p.portalCount / p.speciesCount) * 100;
  const gapsStr = p.hasGaps ? `${p.totalGaps}` : "0";
  
  console.log(
    `${p.name.padEnd(16)} ` +
    `${p.commonName.padEnd(16)} ` +
    `${String(classesCount).padStart(8)} ` +
    `${String(familiesCount).padStart(8)} ` +
    `${p.speciesCount.toLocaleString().padStart(14)} ` +
    `${p.portalCount.toLocaleString().padStart(10)} ` +
    `${p.enrichedCount.toLocaleString().padStart(10)} ` +
    `${gapsStr.padStart(8)} ` +
    `${completePct.toFixed(1).padStart(9)}%`
  );
}
console.log();

// 2. Build Markdown content
let md = `# Phylum-Level Taxonomic Coverage Report\n\n`;
md += `This report aggregates the taxonomic database coverage gaps of the Systema Naturae portal at the **Phylum** level.\n\n`;
md += `*Generated automatically on: ${new Date().toLocaleDateString()}*\n\n`;

md += `## Overview of Phylum Coverage\n\n`;
md += `| Phylum | Common Name | Classes | Families | Imported Species | Total Species Known | Minimal / Empty | Enriched | Completion % | Enrichment % | Gap Status |\n`;
md += `| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n`;

for (const p of sortedPhyla) {
  const classesCount = Object.keys(p.classes).length;
  const familiesCount = Object.values(p.classes).reduce((sum, c) => sum + c.families.length, 0);
  const completionPct = p.speciesCount === 0 ? 100 : (p.portalCount / p.speciesCount) * 100;
  const enrichmentPct = p.speciesCount === 0 ? 100 : (p.enrichedCount / p.speciesCount) * 100;
  const statusIndicator = p.hasGaps ? `> Gaps: ${p.totalGaps}` : `[✓] Complete`;
  
  md += `| **${p.name}** | ${p.commonName} | ${classesCount} | ${familiesCount} | ${p.portalCount.toLocaleString()} | ${p.speciesCount.toLocaleString()} | ${p.minimalCount.toLocaleString()} | ${p.enrichedCount.toLocaleString()} | ${completionPct.toFixed(1)}% | ${enrichmentPct.toFixed(1)}% | ${statusIndicator} |\n`;
}
md += `\n`;

md += `## Detail Breakdown & Checklists by Phylum\n\n`;

for (const p of sortedPhyla) {
  const completionPct = p.speciesCount === 0 ? 100 : (p.portalCount / p.speciesCount) * 100;
  const enrichmentPct = p.speciesCount === 0 ? 100 : (p.enrichedCount / p.speciesCount) * 100;
  
  const box = p.hasGaps ? "[ ]" : "[x]";
  md += `### ${box} Phylum ${p.name} (${p.commonName}) - ${completionPct.toFixed(1)}% complete\n\n`;
  md += `- **Imported species:** ${p.portalCount.toLocaleString()} / ${p.speciesCount.toLocaleString()}\n`;
  md += `- **Enriched species:** ${p.enrichedCount.toLocaleString()} / ${p.speciesCount.toLocaleString()} (${enrichmentPct.toFixed(1)}%)\n`;
  md += `- **Remaining gaps:** ${p.hasGaps ? `**${p.totalGaps}**` : `None! 100% complete`}\n\n`;
  
  md += `#### Child Classes in this Phylum:\n\n`;
  md += `| Class | Families | Imported | Total | Enriched | Completion % | Status |\n`;
  md += `| --- | --- | --- | --- | --- | --- | --- |\n`;
  
  const sortedClassesOfPhylum = Object.values(p.classes).sort((a, b) => {
    // Sort classes with gaps first
    const gapA = a.speciesCount - a.portalCount;
    const gapB = b.speciesCount - b.portalCount;
    return gapB - gapA;
  });

  for (const c of sortedClassesOfPhylum) {
    const cCompletionPct = c.speciesCount === 0 ? 100 : (c.portalCount / c.speciesCount) * 100;
    const cGaps = c.speciesCount - c.portalCount;
    const cStatus = cGaps > 0 ? `> Gaps: ${cGaps}` : `✓ Complete`;
    md += `| ${c.name} | ${c.families.length} | ${c.portalCount.toLocaleString()} | ${c.speciesCount.toLocaleString()} | ${c.enrichedCount.toLocaleString()} | ${cCompletionPct.toFixed(1)}% | ${cStatus} |\n`;
  }
  md += `\n`;
}

const mdPath = join(root, "docs", "gap-tasks-phyla.md");
writeFileSync(mdPath, md, "utf-8");
console.log(`Wrote markdown phylum report to ${mdPath}`);
