/**
 * Bootstrap plant families from a GBIF class cache into plantae/ directory.
 *
 * Reads portal/data/gbif-cache-<classname>.json and generates:
 *   plantae/<class>/<order>/<family>/src/data/<family>.json
 *
 * Usage:
 *   npx tsx scripts/bootstrapPlantae.ts Magnoliopsida 220 299000
 *   npx tsx scripts/bootstrapPlantae.ts Liliopsida 196 93000
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const plantaeRoot = root; // write directly to <root>/<class>/<order>/<family>/... same pattern as animals

const args = process.argv.slice(2);
const [className, classKey, speciesCountStr] = args;
const speciesCount = parseInt(speciesCountStr || "0", 10);

if (!className || !classKey) {
  console.error("Usage: npx tsx scripts/bootstrapPlantae.ts <ClassName> <gbifKey> [speciesCount]");
  console.error("Example: npx tsx scripts/bootstrapPlantae.ts Magnoliopsida 220 299000");
  process.exit(1);
}

const cachePath = resolve(root, "portal", "data", `gbif-cache-${className.toLowerCase()}.json`);
if (!existsSync(cachePath)) {
  console.error(`Cache not found: ${cachePath}. Run cacheGbifClass.ts first.`);
  process.exit(1);
}

const cache = JSON.parse(readFileSync(cachePath, "utf-8"));
console.log(`\n📦 Loaded cache: ${Object.keys(cache.speciesByFamily).length} families\n`);

// Group by order
const orders = new Map<string, { name: string; families: { name: string; count: number }[] }>();
for (const [famName, info] of Object.entries(cache.speciesByFamily as Record<string, any>)) {
  if (!info.species?.length) continue;
  const orderName = (info.species[0] as any).order as string || "Unknown";
  if (!orders.has(orderName)) orders.set(orderName, { name: orderName, families: [] });
  orders.get(orderName)!.families.push({ name: famName, count: info.species.length });
}
console.log(`📊 ${orders.size} orders, ${[...orders.values()].reduce((s, o) => s + o.families.length, 0)} families\n`);

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

function parseScientificName(raw: string): string {
  return raw.replace(/\([^)]*\)/g, "").trim();
}

// Create directories and write data files
console.log(`📁 Creating directories under plantae/...`);
let dirCount = 0;
let generated = 0;
let skipped = 0;
const familiesTotal = [...orders.values()].reduce((s, o) => s + o.families.length, 0);

for (const [orderName, order] of orders) {
  for (const fam of order.families) {
    const slug = fam.name.toLowerCase();
    const dirPath = resolve(plantaeRoot, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data");
    const dataPath = resolve(dirPath, `${slug}.json`);

    if (existsSync(dataPath)) {
      const existing = JSON.parse(readFileSync(dataPath, "utf-8"));
      if (existing.children?.length > 0 || existing.speciesList?.length > 0) {
        skipped++;
        continue;
      }
    }

    mkdirSync(dirPath, { recursive: true });
    dirCount++;

    const info = cache.speciesByFamily[fam.name];
    if (!info || !info.species?.length) {
      writeFileSync(dataPath, JSON.stringify({
        id: makeId(slug, "FAM"),
        name: fam.name,
        rank: "FAMILY",
        commonName: fam.name,
        children: [],
      }, null, 2) + "\n");
      generated++;
      continue;
    }

    // Group by genus
    const genusMap = new Map<string, any[]>();
    for (const sp of info.species) {
      const sciNameRaw = sp.scientificName || sp.species || "";
      const sciName = parseScientificName(sciNameRaw);
      const genusName = sp.genus || sciName.split(" ")[0] || "Unknown";
      if (!sciName || !sciName.includes(" ")) continue;
      if (!genusMap.has(genusName)) genusMap.set(genusName, []);
      genusMap.get(genusName)!.push(sp);
    }

    const children: any[] = [];
    for (const [genusName, spp] of genusMap) {
      const speciesChildren: any[] = [];
      for (const sp of spp) {
        const sciNameRaw = sp.scientificName || sp.species || "";
        const sciName = parseScientificName(sciNameRaw);
        if (!sciName || !sciName.includes(" ")) continue;
        speciesChildren.push({
          id: nameToId(sciName),
          name: sciName,
          rank: "SPECIES",
          lineage: genusName,
          subspeciesCount: 0,
          description: `${sciName} — a ${className.toLowerCase()} species in the genus ${genusName}.`,
          sourcedFrom: "generated",
        });
      }
      speciesChildren.sort((a, b) => a.name.localeCompare(b.name));
      children.push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of ${className.toLowerCase()}s.`,
        lineage: genusName,
        children: speciesChildren,
      });
    }

    writeFileSync(dataPath, JSON.stringify({
      id: makeId(slug, "FAM"),
      name: fam.name,
      rank: "FAMILY",
      commonName: fam.name,
      children,
    }, null, 2) + "\n");
    generated++;
    if (generated % 50 === 0) process.stdout.write(`   ${generated}/${familiesTotal}\r`);
  }
}

console.log(`\n\n✅ Done: ${generated} generated, ${skipped} skipped, ${dirCount} directories`);
console.log(`   Location: plantae/${className.toLowerCase()}/`);
