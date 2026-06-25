import { readFileSync, writeFileSync, existsSync, readdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const backupPath = resolve(__dirname, "../data/namedafter-backup.json");

interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  namedAfter?: string;
  children?: TaxonNode[];
}

const backup: Record<string, Record<string, string>> = JSON.parse(readFileSync(backupPath, "utf-8"));
let totalMerged = 0;
let totalFiles = 0;

function findAndStamp(node: TaxonNode, speciesMap: Record<string, string>): boolean {
  let modified = false;
  if (node.rank === "SPECIES" && speciesMap[node.name]) {
    node.namedAfter = speciesMap[node.name];
    modified = true;
  }
  if (node.children) {
    for (const c of node.children) {
      if (findAndStamp(c, speciesMap)) modified = true;
    }
  }
  return modified;
}

// Find all family data files
const classEntries = [
  "actinopterygii", "amphibia", "arachnida", "asteroidea", "aves",
  "cephalopoda", "chondrichthyes", "echinoidea", "holothuroidea",
  "insecta", "mammalia", "reptilia",
];

for (const cls of classEntries) {
  const classDir = resolve(root, cls);
  if (!existsSync(classDir)) continue;
  const orders = readdirSync(classDir).filter(f => !f.startsWith("."));
  for (const ord of orders) {
    const orderDir = resolve(classDir, ord);
    if (!existsSync(orderDir)) continue;
    const families = readdirSync(orderDir).filter(f => !f.startsWith("."));
    for (const slug of families) {
      if (!backup[slug]) continue;
      const dataFile = resolve(orderDir, slug, "src", "data", `${slug}.json`);
      if (!existsSync(dataFile)) continue;
      try {
        const raw = JSON.parse(readFileSync(dataFile, "utf-8")) as TaxonNode;
        const modified = findAndStamp(raw, backup[slug]);
        if (modified) {
          writeFileSync(dataFile, JSON.stringify(raw, null, 2) + "\n");
          totalMerged += Object.keys(backup[slug]).length;
          totalFiles++;
        }
      } catch (e) {
        console.error(`  ⚠ Error processing ${slug}: ${e}`);
      }
    }
  }
}

// Tardigrada at root
const tardigradaFile = resolve(root, "tardigrada", "src", "data", "tardigrada.json");
if (backup["tardigrada"] && existsSync(tardigradaFile)) {
  try {
    const raw = JSON.parse(readFileSync(tardigradaFile, "utf-8")) as TaxonNode;
    if (findAndStamp(raw, backup["tardigrada"])) {
      writeFileSync(tardigradaFile, JSON.stringify(raw, null, 2) + "\n");
      totalMerged += Object.keys(backup["tardigrada"]).length;
      totalFiles++;
    }
  } catch (e) {
    console.error(`  ⚠ Error processing tardigrada: ${e}`);
  }
}

console.log(`✅ Merged namedAfter entries into ${totalFiles} files (${totalMerged} species)`);
