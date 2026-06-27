import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE_PATH = resolve(root, "portal", "data", "gbif-cache-hydrozoa.json");
const TAX_PATH = resolve(root, "portal", "data", "taxonomy.json");
const COLOR_PATH = resolve(root, "portal", "src", "colorRegistry.ts");

interface GbifCache {
  speciesByFamily: Record<string, { gbifKey: number; species: Record<string, unknown>[] }>;
}

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

// ── 1. Read cache ──
const cache: GbifCache = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));

// Group by order
const orders = new Map<string, { name: string; families: { name: string; count: number }[] }>();
for (const [famName, info] of Object.entries(cache.speciesByFamily)) {
  if (!info.species?.length) continue;
  const orderName = (info.species[0] as Record<string, unknown>).order as string || "Unknown";
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
console.log("📁 Creating directories...");
let dirCount = 0;
for (const [orderName, order] of sortedOrders()) {
  for (const fam of order.families) {
    const slug = fam.name.toLowerCase();
    const dirPath = resolve(root, "hydrozoa", orderName.toLowerCase(), slug, "src", "data");
    mkdirSync(dirPath, { recursive: true });
    dirCount++;
  }
}
console.log(`   Created ${dirCount} directories`);

// ── 3. Insert into taxonomy.json ──
console.log("\n📝 Updating taxonomy.json...");
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

const hydrozoaEntry = {
  id: "HYDROZOA",
  name: "Hydrozoa",
  rank: "CLASS",
  commonName: "Hydrozoans",
  description: "Hydrozoans — a diverse class of cnidarians including hydras, siphonophores (such as the Portuguese man o' war), and many colonial hydroids. They exhibit remarkable morphological diversity, with some species entirely lacking a medusa stage and others forming complex floating colonies.",
  speciesCount: 4505,
  children: sortedOrders().map(([, order]) => ({
    id: makeId(order.name, "HYDROZOA"),
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

// Find and replace the existing Hydrozoa entry
const hydroIdx = cnidaria.children.findIndex((c: any) => c.id === "HYDROZOA");
if (hydroIdx >= 0) {
  cnidaria.children[hydroIdx] = hydrozoaEntry;
} else {
  // Insert after Cubozoa (index 0) and before Scyphozoa
  cnidaria.children.splice(1, 0, hydrozoaEntry);
}

writeFileSync(TAX_PATH, JSON.stringify(tax, null, 2) + "\n");
console.log(`   Updated taxonomy.json with Hydrozoa class (${[...orders.values()].reduce((s, o) => s + o.families.length, 0)} families)`);

// ── 4. Update colorRegistry.ts ──
console.log("\n🎨 Updating colorRegistry.ts...");
const colorTs = readFileSync(COLOR_PATH, "utf-8");

// Generate all theme constants
const palette = [
  "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
  "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
  "#06B6D4", "#D946EF", "#0EA5E9", "#22C55E", "#EAB308",
  "#A855F7", "#FB923C", "#2DD4BF", "#A3E635", "#38BDF8",
];

let colorIdx = 1;
const themeLines: string[] = [];
const registerLines: string[] = [];
const typeDeclarations: string[] = [];

for (const [, order] of sortedOrders()) {
  for (const fam of order.families.sort((a, b) => b.count - a.count)) {
    const slug = fam.name.toLowerCase();
    const constName = `hydrozoa_${slug}`;
    const c = palette[colorIdx % palette.length];
    const lc = palette[(colorIdx + 5) % palette.length];
    colorIdx++;

    typeDeclarations.push(`${constName}: ColorTheme`);
    themeLines.push(`const ${constName}: ColorTheme = { subfamilyColors: {}, breedGroupColor: "${c}", hybridColor: "${lc}", appSlug: "${slug}", className: "Hydrozoa", orderName: "${order.name}", name: "${fam.name}", mainColor: "${c}", lineageColors: { "${slug}": "${lc}" } };`);
    registerLines.push(`  "${slug}": ${constName},`);
  }
}

// Insert theme constants before the COLOR_REGISTRY
const registryMarker = "export const COLOR_REGISTRY: Record<string, ColorTheme> = {";
const themeInsertion = `\n// ── Hydrozoa (${[...orders.values()].reduce((s, o) => s + o.families.length, 0)} families) ──\n${themeLines.join("\n")}\n\n`;

const beforeRegistry = colorTs.substring(0, colorTs.lastIndexOf(registryMarker));
const afterRegistry = colorTs.substring(colorTs.lastIndexOf(registryMarker));

// Find the last entry before closing brace of COLOR_REGISTRY
const registryEnd = afterRegistry.indexOf("};", registryMarker.length);
const registryBody = afterRegistry.substring(registryMarker.length, registryEnd);
const updatedRegistry = afterRegistry.substring(0, registryMarker.length) + registryBody + "\n" + registerLines.join("\n") + afterRegistry.substring(registryEnd);

writeFileSync(COLOR_PATH, beforeRegistry + themeInsertion + updatedRegistry);
console.log(`   Added ${themeLines.length} color themes to colorRegistry.ts`);

// ── 5. Run fetch for all families ──
console.log("\n🌊 Fetching Hydrozoa families from cache...");
const allSlugs = [...orders.values()].flatMap(o => o.families.map(f => f.name.toLowerCase()));
let fetched = 0;
let failed = 0;

for (const slug of allSlugs) {
  try {
    const result = execSync(
      `NO_WIKI=1 npx tsx portal/scripts/fetchSpeciesFromApi.ts ${slug} 2>/dev/null`,
      { cwd: root, encoding: "utf-8", timeout: 60000 }
    );
    fetched++;
    process.stdout.write(".");
    if (fetched % 20 === 0) console.log(` ${fetched}/${allSlugs.length}`);
  } catch (e) {
    failed++;
    process.stdout.write("x");
  }
}

console.log(`\n\n✅ Done: ${fetched} families fetched, ${failed} failed`);
