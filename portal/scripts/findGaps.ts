import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");

const enriched = new Set([
  "apidae", "salticidae", "colubridae", "araneidae", "theridiidae",
  "lycosidae", "cyprinidae", "scincidae", "tardigrada", "buthidae",
  "gekkonidae", "theraphosidae", "hylidae", "cricetidae", "muridae",
  "microhylidae", "bufonidae", "agamidae", "plethodontidae", "soricidae",
  "ranidae"
]);

interface FamilyInfo {
  className: string;
  orderName: string;
  appSlug: string;
  name: string;
  speciesCount: number;
  portalCount: number;
  gap: number;
  dataFilePath: string;
}

function walk(node: any, className: string, orderName: string, results: FamilyInfo[]) {
  if (!node || typeof node !== "object") return;
  const children = node.children || [];
  if (node.rank === "CLASS") {
    className = node.name;
  }
  if (node.rank === "ORDER") {
    orderName = node.name;
  }
  if (node.rank === "FAMILY" && node.appSlug && node.speciesCount != null) {
    if (!enriched.has(node.appSlug)) {
      let dataFilePath: string;
      if (node.appSlug === "tardigrada") {
        dataFilePath = join(root, "tardigrada", "src", "data", "tardigrada.json");
      } else {
        const cls = className.toLowerCase().replace(/\s+/g, "_");
        const ord = orderName.toLowerCase().replace(/\s+/g, "_");
        dataFilePath = join(root, cls, ord, node.appSlug, "src", "data", `${node.appSlug}.json`);
      }
      results.push({
        className,
        orderName,
        appSlug: node.appSlug,
        name: node.commonName || node.name,
        speciesCount: node.speciesCount,
        portalCount: 0,
        gap: 0,
        dataFilePath
      });
    }
    return; // don't descend into family children in taxonomy
  }
  if (Array.isArray(children)) {
    for (const child of children) {
      walk(child, className, orderName, results);
    }
  }
}

function countSpecies(data: any): number {
  if (!data || typeof data !== "object") return 0;
  let count = 0;
  if (data.rank === "SPECIES") count++;
  const children = data.children;
  if (Array.isArray(children)) {
    for (const child of children) {
      count += countSpecies(child);
    }
  }
  return count;
}

const taxonomy = JSON.parse(readFileSync(join(root, "portal", "data", "taxonomy.json"), "utf-8"));
const results: FamilyInfo[] = [];
walk(taxonomy, "", "", results);

for (const r of results) {
  if (existsSync(r.dataFilePath)) {
    const data = JSON.parse(readFileSync(r.dataFilePath, "utf-8"));
    r.portalCount = countSpecies(data);
  } else {
    r.portalCount = 0;
  }
  r.gap = r.speciesCount - r.portalCount;
}

results.sort((a, b) => b.gap - a.gap);

const top15 = results.slice(0, 15);

console.log();
console.log(`${"#".padEnd(3)} ${"Class".padEnd(22)} ${"Order".padEnd(24)} ${"Family".padEnd(28)} ${"appSlug".padEnd(22)} ${"speciesCount".padEnd(14)} ${"portalCount".padEnd(13)} ${"Gap".padEnd(6)}`);
console.log("-".repeat(132));
top15.forEach((r, i) => {
  console.log(`${String(i + 1).padEnd(3)} ${r.className.padEnd(22)} ${r.orderName.padEnd(24)} ${r.name.padEnd(28)} ${r.appSlug.padEnd(22)} ${String(r.speciesCount).padEnd(14)} ${String(r.portalCount).padEnd(13)} ${String(r.gap).padEnd(6)}`);
  console.log(`    ${r.dataFilePath}`);
  console.log();
});
