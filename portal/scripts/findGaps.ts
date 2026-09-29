import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { resolveFamilyFile } from "./lib/familyPath.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");
const portalRoot = join(root, "portal");

// ── Kingdom selection (mirrors buildData.ts) ──
// SN_KINGDOM picks the kingdom (default: animalia). Input taxonomy + output
// report path are derived from data/kingdom-config.json so gap analysis stays
// consistent with the build.
const KINGDOM = process.env.SN_KINGDOM || "";
const kingdomConfigPath = join(portalRoot, "data", "kingdom-config.json");
let kingdomConfig: { input?: string; dataSuffix?: string } | undefined;
if (existsSync(kingdomConfigPath)) {
  const allConfigs = JSON.parse(readFileSync(kingdomConfigPath, "utf-8"));
  kingdomConfig = allConfigs.kingdoms?.[KINGDOM];
}
const dataSuffix = kingdomConfig?.dataSuffix ?? (KINGDOM ? `-${KINGDOM}` : "");
const taxonomyInput = kingdomConfig?.input ?? process.env.SN_INPUT ?? "data/taxonomy.json";

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

function walk(
  node: any,
  className: string,
  orderName: string,
  results: FamilyInfo[],
  phylumName = "",
  hasClass: boolean = false,
) {
  if (!node || typeof node !== "object") return;
  const children = node.children || [];
  if (node.rank === "CLASS") {
    className = node.name;
    hasClass = true;
  }
  if (node.rank === "PHYLUM") {
    phylumName = node.name;
    // Legacy on-disk shape: a phylum with no class is a top-level directory,
    // and a phylum whose class shares its name is a directory containing a
    // directory of the same name (xenacoelomorpha/acoela/...).
    if (!className) className = node.name;
  }
  if (node.rank === "ORDER") {
    orderName = node.name;
  }
  if (node.rank === "FAMILY" && node.appSlug && node.speciesCount != null) {
    // Resolved by the shared helper rather than rebuilt here. This used to be a
    // second, different implementation of the same rule - `hasClass` deciding
    // between [class, order, family] and [family] - which is exactly the kind
    // of divergence that fails silently: a wrong path makes existsSync false,
    // portalCount becomes 0, and gap becomes speciesCount for every family,
    // so the whole gap report is rewritten as garbage with no error.
    const { file: dataFilePath } = resolveFamilyFile(root, {
      kingdom: KINGDOM || undefined,
      phylum: phylumName || undefined,
      cls: hasClass ? className : undefined,
      ord: orderName || undefined,
      slug: node.appSlug,
    });
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
      walk(child, className, orderName, results, phylumName, hasClass);
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

const taxonomyPath = join(portalRoot, taxonomyInput);
const taxonomy = JSON.parse(readFileSync(taxonomyPath, "utf-8"));
console.log(`Analyzing kingdom ${KINGDOM || "animalia"} from ${taxonomyPath}`);
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

// Write the complete gap report to JSON (per-kingdom: gap-report.json,
// gap-report-plantae.json, …)
const reportPath = join(portalRoot, "data", `gap-report${dataSuffix}.json`);
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
