import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");

interface FamilyInfo {
  className: string;
  orderName: string;
  appSlug: string;
  name: string;
  speciesCount: number;
  portalCount: number;
  minimalCount: number;
  enrichedCount: number;
  gap: number;
  trueGap: number;
  dataFilePath: string;
}

function walk(node: any, className: string, orderName: string, results: FamilyInfo[]) {
  if (!node || typeof node !== "object") return;
  const children = node.children || [];
  if (node.rank === "CLASS" || (node.rank === "PHYLUM" && !className)) {
    className = node.name;
  }
  if (node.rank === "ORDER") {
    orderName = node.name;
  }
  if (node.rank === "FAMILY" && node.appSlug && node.speciesCount != null) {
    let dataFilePath: string;
    const cls = className ? className.toLowerCase().replace(/\s+/g, "_") : "";
    const ord = orderName ? orderName.toLowerCase().replace(/\s+/g, "_") : "";
    const parts = [cls, ord, node.appSlug].filter(Boolean);
    dataFilePath = join(root, ...parts, "src", "data", `${node.appSlug}.json`);
    results.push({
      className,
      orderName,
      appSlug: node.appSlug,
      name: node.commonName || node.name,
      speciesCount: node.speciesCount,
      portalCount: 0,
      minimalCount: 0,
      enrichedCount: 0,
      gap: 0,
      trueGap: 0,
      dataFilePath
    });
    return; // don't descend into family children in taxonomy
  }
  if (Array.isArray(children)) {
    for (const child of children) {
      walk(child, className, orderName, results);
    }
  }
}

function analyzeSpecies(data: any): { total: number; minimal: number; enriched: number } {
  let total = 0;
  let minimal = 0;
  let enriched = 0;

  function walk(node: any) {
    if (!node || typeof node !== "object") return;

    if (node.rank === "SPECIES") {
      total++;
      const desc = node.description || "";
      const isMin = !desc || desc.toLowerCase().includes("a species in the genus") || desc.trim().length < 20;
      if (isMin) {
        minimal++;
      } else {
        enriched++;
      }
    }

    if (Array.isArray(node.children)) {
      for (const child of node.children) {
        walk(child);
      }
    }

    if (Array.isArray(node.speciesList)) {
      for (const sp of node.speciesList) {
        total++;
        const desc = sp.description || "";
        const isMin = !desc || desc.toLowerCase().includes("a species in the genus") || desc.trim().length < 20;
        if (isMin) {
          minimal++;
        } else {
          enriched++;
        }
      }
    }
  }

  walk(data);
  return { total, minimal, enriched };
}

const taxonomy = JSON.parse(readFileSync(join(root, "portal", "data", "taxonomy.json"), "utf-8"));
const results: FamilyInfo[] = [];
walk(taxonomy, "", "", results);

for (const r of results) {
  if (existsSync(r.dataFilePath)) {
    const data = JSON.parse(readFileSync(r.dataFilePath, "utf-8"));
    const stats = analyzeSpecies(data);
    r.portalCount = stats.total;
    r.minimalCount = stats.minimal;
    r.enrichedCount = stats.enriched;
  } else {
    r.portalCount = 0;
    r.minimalCount = 0;
    r.enrichedCount = 0;
  }
  r.gap = r.speciesCount - r.portalCount;
  r.trueGap = r.speciesCount - r.enrichedCount;
}

// Write the complete gap report to JSON
const reportPath = join(root, "portal", "data", "gap-report.json");
writeFileSync(reportPath, JSON.stringify(results, null, 2), "utf-8");
console.log(`Wrote full gap report to ${reportPath}`);

// Sort by gap size for printing
results.sort((a, b) => b.gap - a.gap);

const top15 = results.slice(0, 15);

console.log();
console.log(`${"#".padEnd(3)} ${"Class".padEnd(22)} ${"Order".padEnd(24)} ${"Family".padEnd(28)} ${"appSlug".padEnd(22)} ${"speciesCount".padEnd(14)} ${"portalCount".padEnd(13)} ${"Enriched".padEnd(10)} ${"Gap".padEnd(6)}`);
console.log("-".repeat(142));
top15.forEach((r, i) => {
  console.log(`${String(i + 1).padEnd(3)} ${r.className.padEnd(22)} ${r.orderName.padEnd(24)} ${r.name.padEnd(28)} ${r.appSlug.padEnd(22)} ${String(r.speciesCount).padEnd(14)} ${String(r.portalCount).padEnd(13)} ${String(r.enrichedCount).padEnd(10)} ${String(r.gap).padEnd(6)}`);
  console.log(`    ${r.dataFilePath}`);
  console.log();
});
