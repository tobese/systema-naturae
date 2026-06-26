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

// Group by class
interface ClassStats {
  className: string;
  classSlug: string;
  families: any[];
  speciesCount: number;
  portalCount: number;
  minimalCount: number;
  enrichedCount: number;
  totalGaps: number;
  hasGaps: boolean;
}

const classGroups: Record<string, ClassStats> = {};

for (const f of families) {
  const className = f.className || "Other";
  if (!classGroups[className]) {
    classGroups[className] = {
      className,
      classSlug: className.toLowerCase().replace(/\s+/g, "_"),
      families: [],
      speciesCount: 0,
      portalCount: 0,
      minimalCount: 0,
      enrichedCount: 0,
      totalGaps: 0,
      hasGaps: false
    };
  }
  const group = classGroups[className];
  group.families.push(f);
  group.speciesCount += f.speciesCount || 0;
  group.portalCount += f.portalCount || 0;
  group.minimalCount += f.minimalCount || 0;
  group.enrichedCount += f.enrichedCount || 0;
  
  if (f.portalCount < f.speciesCount) {
    group.hasGaps = true;
    group.totalGaps += (f.speciesCount - f.portalCount);
  }
}

// Convert to array and sort by CLASS_RANK
const CLASS_RANK: Record<string, number> = {
  "mammalia": 1,
  "aves": 2,
  "reptilia": 3,
  "amphibia": 4,
  "chondrichthyes": 5,
  "actinopterygii": 6,
  "cephalopoda": 7,
  "asteroidea": 8,
  "echinoidea": 9,
  "holothuroidea": 10,
  "scyphozoa": 11,
  "cubozoa": 12,
  "staurozoa": 13,
  "anthozoa": 14,
  "hydrozoa": 15,
  "tentaculata": 16,
  "nuda": 17,
  "arachnida": 18,
  "insecta": 19
};

const sortedClasses = Object.values(classGroups).sort((a, b) => {
  const rA = CLASS_RANK[a.classSlug] ?? 999;
  const rB = CLASS_RANK[b.classSlug] ?? 999;
  return rA - rB;
});

// Build docs/gap-tasks.md Checklist
let md = `# Biological Database Gap Tasks\n\n`;
md += `This file tracks the taxonomic coverage gaps and enrichment tasks of the Systema Naturae portal. Each class with remaining gaps has a discrete checklist of its families.\n\n`;
md += `*Generated automatically on: ${new Date().toLocaleDateString()}*\n\n`;

md += `## Overview of Taxonomic Class Coverage\n\n`;
md += `| Class | Size Sort Rank | Imported Species | Total Species Known | Minimal / Empty | Enriched | Completion % | Enrichment % | Gap Status |\n`;
md += `| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n`;

for (const cls of sortedClasses) {
  const completionPct = cls.speciesCount === 0 ? 100 : (cls.portalCount / cls.speciesCount) * 100;
  const enrichmentPct = cls.speciesCount === 0 ? 100 : (cls.enrichedCount / cls.speciesCount) * 100;
  const statusIndicator = cls.hasGaps ? `> Gaps: ${cls.totalGaps}` : `[✓] Complete`;
  md += `| **${cls.className}** | ${CLASS_RANK[cls.classSlug] ?? "Other"} | ${cls.portalCount.toLocaleString()} | ${cls.speciesCount.toLocaleString()} | ${cls.minimalCount.toLocaleString()} | ${cls.enrichedCount.toLocaleString()} | ${completionPct.toFixed(1)}% | ${enrichmentPct.toFixed(1)}% | ${statusIndicator} |\n`;
}
md += `\n`;

// Detail lists for classes with remaining gaps
md += `## Discrete Gap Checklists by Class\n\n`;

for (const cls of sortedClasses) {
  if (!cls.hasGaps) {
    md += `### [x] ${cls.className} (100% complete)\n\nAll families in this class are fully imported into the portal. Nice!\n\n`;
    continue;
  }

  const completionPct = cls.speciesCount === 0 ? 100 : (cls.portalCount / cls.speciesCount) * 100;
  const enrichmentPct = cls.speciesCount === 0 ? 100 : (cls.enrichedCount / cls.speciesCount) * 100;
  
  md += `### [ ] ${cls.className} Gap Enrichment (${completionPct.toFixed(1)}% imported, ${enrichmentPct.toFixed(1)}% enriched)\n\n`;
  md += `Remaining Gaps in Class: **${cls.totalGaps}** species missing from portal.\n\n`;
  
  // Sort families within class: families with gaps first, then by gap size descending
  const sortedFamilies = [...cls.families].sort((a, b) => {
    const gapA = a.speciesCount - a.portalCount;
    const gapB = b.speciesCount - b.portalCount;
    if (gapA !== gapB) {
      return gapB - gapA; // larger gap first
    }
    return a.name.localeCompare(b.name);
  });

  for (const f of sortedFamilies) {
    const isComplete = f.portalCount >= f.speciesCount;
    const gap = f.speciesCount - f.portalCount;
    const box = isComplete ? "[x]" : "[ ]";
    const details = isComplete 
      ? `(Complete: ${f.portalCount}/${f.speciesCount} imported)`
      : `(Gaps: **${gap}** species missing - ${f.portalCount}/${f.speciesCount} imported, ${f.minimalCount} empty, ${f.enrichedCount} enriched)`;
    
    md += `- ${box} **${f.name}** (\`${f.appSlug}\`) ${details}\n`;
  }
  md += `\n`;
}

const mdPath = join(root, "docs", "gap-tasks.md");
writeFileSync(mdPath, md, "utf-8");
console.log(`Wrote markdown task board to ${mdPath}`);

// Sync to local progressd daemon
const progressdUrl = process.env.PROGRESSD_URL || "http://localhost:9876";
console.log(`Connecting to progressd daemon at ${progressdUrl}...`);

for (const cls of sortedClasses) {
  const sessionId = `gap_${cls.classSlug}`;
  const label = `${cls.className} Gap Enrichment`;
  const completionPct = cls.speciesCount === 0 ? 100 : (cls.portalCount / cls.speciesCount) * 100;
  
  if (!cls.hasGaps) {
    const message = `${cls.portalCount}/${cls.speciesCount} species imported (0 gaps)`;
    try {
      const payload = {
        message,
        pct: 100,
        done: true,
        label
      };
      
      const res = await fetch(`${progressdUrl}/api/sessions/${sessionId}/progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        console.log(`[${cls.className}] Marked as 100% complete in progressd.`);
      } else {
        console.log(`[${cls.className}] progressd update skipped or completed (HTTP ${res.status})`);
      }
    } catch (e: any) {
      console.warn(`[${cls.className}] Failed to update progressd: ${e.message}`);
    }
    continue;
  }

  const message = `${cls.portalCount}/${cls.speciesCount} species imported (${cls.minimalCount} empty)`;

  try {
    const payload = {
      message,
      pct: parseFloat(completionPct.toFixed(2)),
      done: false,
      label
    };

    const res = await fetch(`${progressdUrl}/api/sessions/${sessionId}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      console.log(`[${cls.className}] Session updated in progressd: ${completionPct.toFixed(1)}% complete - ${message}`);
    } else {
      console.error(`[${cls.className}] Failed to update session in progressd: ${res.status} ${res.statusText}`);
    }
  } catch (e: any) {
    console.warn(`[${cls.className}] Failed to send progress to progressd: ${e.message}`);
  }
}
