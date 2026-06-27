import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const args = process.argv.slice(2);
const className = args[0] || "Anthozoa";
const classKey = parseInt(args[1] || "206", 10);
const classId = args[2] || className.toUpperCase();

const CACHE_PATH = resolve(root, "portal", "data", `gbif-cache-${className.toLowerCase()}.json`);
const TAX_PATH = resolve(root, "portal", "data", "taxonomy.json");
const COLOR_PATH = resolve(root, "portal", "src", "colorRegistry.ts");

if (!existsSync(CACHE_PATH)) {
  console.error(`Cache not found: ${CACHE_PATH}`);
  console.error("Run scripts/cacheGbifClass.ts first");
  process.exit(1);
}

const cache = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

function parseScientificName(raw: string): string {
  return raw.replace(/\([^)]*\)/g, "").trim();
}

// ── 1. Group by order ──
const orders = new Map<string, { name: string; families: { name: string; count: number }[] }>();
for (const [famName, info] of Object.entries(cache.speciesByFamily)) {
  const firstSpecies = info.species[0];
  const orderName = firstSpecies?.order || "Unknown";
  if (!orders.has(orderName)) orders.set(orderName, { name: orderName, families: [] });
  orders.get(orderName)!.families.push({ name: famName, count: info.species.length });
}

function sortedOrders() {
  return [...orders.entries()].sort((a, b) => {
    const totalA = a[1].families.reduce((s, f) => s + f.count, 0);
    const totalB = b[1].families.reduce((s, f) => s + f.count, 0);
    return totalB - totalA;
  });
}

// ── 2. Create directories ──
console.log(`📁 Creating directories for ${className}...`);
let dirCount = 0;
for (const [orderName, order] of sortedOrders()) {
  for (const fam of order.families) {
    const slug = fam.name.toLowerCase();
    const dirPath = resolve(root, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data");
    mkdirSync(dirPath, { recursive: true });
    dirCount++;
  }
}
console.log(`   Created ${dirCount} directories`);

// ── 3. Insert into taxonomy.json ──
console.log(`\n📝 Updating taxonomy.json...`);
const tax = JSON.parse(readFileSync(TAX_PATH, "utf-8"));

function findCnidariaPhylum(node: any): any {
  if (node.id === "CNIDARIA") return node;
  for (const c of (node.children ?? [])) {
    const found = findCnidariaPhylum(c);
    if (found) return found;
  }
  return null;
}

const cnidaria = findCnidariaPhylum(tax);
if (!cnidaria) { console.error("CNIDARIA not found!"); process.exit(1); }

const totalSpeciesCount = Object.values(cache.speciesByFamily).reduce((s: number, v: any) => s + v.species.length, 0);

const classEntry = {
  id: classId,
  name: className,
  rank: "CLASS",
  commonName: `${className}`,
  speciesCount: totalSpeciesCount,
  children: sortedOrders().map(([, order]) => ({
    id: makeId(order.name, classId),
    name: order.name,
    rank: "ORDER",
    commonName: order.name,
    children: order.families.sort((a, b) => b.count - a.count).map(fam => ({
      id: makeId(fam.name, "FAM"),
      name: fam.name,
      rank: "FAMILY",
      commonName: fam.name,
      appSlug: fam.name.toLowerCase(),
      speciesCount: fam.count,
    })),
  })),
};

const clsIdx = cnidaria.children.findIndex((c: any) => c.id === classId);
if (clsIdx >= 0) {
  cnidaria.children[clsIdx] = classEntry;
} else {
  cnidaria.children.push(classEntry);
}

writeFileSync(TAX_PATH, JSON.stringify(tax, null, 2) + "\n");
console.log(`   Updated taxonomy.json with ${className} class (${sortedOrders().reduce((s, [,o]) => s + o.families.length, 0)} families)`);

// ── 4. Update colorRegistry.ts ──
console.log(`\n🎨 Updating colorRegistry.ts...`);
const colorTs = readFileSync(COLOR_PATH, "utf-8");

const palette = [
  "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
  "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
  "#06B6D4", "#D946EF", "#0EA5E9", "#22C55E", "#EAB308",
  "#A855F7", "#FB923C", "#2DD4BF", "#A3E635", "#38BDF8",
];

let colorIdx = 1;
const themeLines: string[] = [];
const registerLines: string[] = [];

for (const [, order] of sortedOrders()) {
  for (const fam of order.families.sort((a, b) => b.count - a.count)) {
    const slug = fam.name.toLowerCase();
    const constName = `${className.toLowerCase()}_${slug}`;
    const c = palette[colorIdx % palette.length];
    const lc = palette[(colorIdx + 5) % palette.length];
    colorIdx++;
    themeLines.push(`const ${constName}: ColorTheme = { subfamilyColors: {}, breedGroupColor: "${c}", hybridColor: "${lc}", appSlug: "${slug}", className: "${className}", orderName: "${order.name}", name: "${fam.name}", mainColor: "${c}", lineageColors: { "${slug}": "${lc}" } };`);
    registerLines.push(`  "${slug}": ${constName},`);
  }
}

const registryMarker = "export const COLOR_REGISTRY: Record<string, ColorTheme> = {";
const themeHeader = `\n// ── ${className} (${sortedOrders().reduce((s, [,o]) => s + o.families.length, 0)} families) ──\n`;
const themeInsertion = themeHeader + themeLines.join("\n") + "\n\n";

const beforeRegistry = colorTs.substring(0, colorTs.lastIndexOf(registryMarker));
const afterRegistry = colorTs.substring(colorTs.lastIndexOf(registryMarker));
const registryEnd = afterRegistry.indexOf("};", registryMarker.length);
const registryBody = afterRegistry.substring(registryMarker.length, registryEnd);
const updatedRegistry = afterRegistry.substring(0, registryMarker.length) + registryBody + "\n" + registerLines.join("\n") + afterRegistry.substring(registryEnd);

writeFileSync(COLOR_PATH, beforeRegistry + themeInsertion + updatedRegistry);
console.log(`   Added ${themeLines.length} color themes to colorRegistry.ts`);

// ── 5. Generate data files from cache ──
console.log(`\n📄 Generating data files from cache...`);
const familiesTotal = sortedOrders().reduce((s, [,o]) => s + o.families.length, 0);
let generated = 0;
let skipped = 0;

for (const [orderName, order] of sortedOrders()) {
  for (const fam of order.families) {
    const slug = fam.name.toLowerCase();
    const dataPath = resolve(root, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data", `${slug}.json`);

    if (existsSync(dataPath)) {
      const existing = JSON.parse(readFileSync(dataPath, "utf-8"));
      if (existing.children?.length > 0 || existing.speciesList?.length > 0) {
        skipped++;
        continue;
      }
    }

    const info = cache.speciesByFamily[fam.name];
    if (!info || !info.species.length) {
      const dir = resolve(root, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data");
      mkdirSync(dir, { recursive: true });
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
        const speciesEpithet = sciName.split(" ").slice(1).join("_") || "sp";
        speciesChildren.push({
          id: nameToId(sciName),
          name: sciName,
          rank: "SPECIES",
          commonName: `${genusName} ${speciesEpithet}`.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
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

    const dir = resolve(root, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data");
    mkdirSync(dir, { recursive: true });
    writeFileSync(dataPath, JSON.stringify({
      id: makeId(slug, "FAM"),
      name: fam.name,
      rank: "FAMILY",
      commonName: fam.name,
      children,
    }, null, 2) + "\n");
    generated++;
    if (generated % 50 === 0) console.log(`   ${generated}/${familiesTotal}`);
  }
}

console.log(`\n✅ Done: ${generated} generated, ${skipped} skipped (${familiesTotal} total)`);
