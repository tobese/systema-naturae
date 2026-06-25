import { readFileSync, writeFileSync, existsSync, readdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const outPath = resolve(__dirname, "../data/namedafter-backup.json");

interface FamilyData {
  id: string;
  name: string;
  rank: string;
  commonName: string;
  children: unknown[];
}

interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  namedAfter?: string;
  children?: TaxonNode[];
}

function walkSpecies(node: TaxonNode, map: Record<string, string>): void {
  if (node.rank === "SPECIES" && node.namedAfter) {
    map[node.name] = node.namedAfter;
  }
  if (node.children) {
    for (const c of node.children) walkSpecies(c, map);
  }
}

const backup: Record<string, Record<string, string>> = {};

// Find all family data files under class directories
const rootDir = root;
const entries = [
  "actinopterygii", "amphibia", "arachnida", "asteroidea", "aves",
  "cephalopoda", "chondrichthyes", "echinoidea", "holothuroidea",
  "insecta", "mammalia", "reptilia", "tardigrada",
];

for (const cls of entries) {
  const classDir = resolve(rootDir, cls);
  if (!existsSync(classDir)) continue;
  const orders = readdirSync(classDir).filter(f => !f.startsWith("."));
  for (const ord of orders) {
    const orderDir = resolve(classDir, ord);
    if (!existsSync(orderDir)) continue;
    // Each order contains family subdirectories
    const families = readdirSync(orderDir).filter(f => !f.startsWith("."));
    for (const slug of families) {
      const dataFile = resolve(orderDir, slug, "src", "data", `${slug}.json`);
      if (!existsSync(dataFile)) continue;
      try {
        const raw = JSON.parse(readFileSync(dataFile, "utf-8")) as FamilyData;
        const speciesMap: Record<string, string> = {};
        if (raw.children) {
          for (const c of raw.children as TaxonNode[]) walkSpecies(c, speciesMap);
        }
        if (Object.keys(speciesMap).length > 0) {
          backup[slug] = speciesMap;
        }
      } catch { /* skip unparseable */ }
    }
  }
}

// Also handle tardigrada at root
const tardigradaFile = resolve(rootDir, "tardigrada", "src", "data", "tardigrada.json");
if (existsSync(tardigradaFile)) {
  try {
    const raw = JSON.parse(readFileSync(tardigradaFile, "utf-8")) as FamilyData;
    const speciesMap: Record<string, string> = {};
    if (raw.children) {
      for (const c of raw.children as TaxonNode[]) walkSpecies(c, speciesMap);
    }
    if (Object.keys(speciesMap).length > 0) {
      backup["tardigrada"] = speciesMap;
    }
  } catch { /* skip */ }
}

writeFileSync(outPath, JSON.stringify(backup, null, 2) + "\n");
const totalFamilies = Object.keys(backup).length;
const totalSpecies = Object.values(backup).reduce((s, m) => s + Object.keys(m).length, 0);
console.log(`✅ Extracted ${totalSpecies} namedAfter entries across ${totalFamilies} families → ${outPath}`);
