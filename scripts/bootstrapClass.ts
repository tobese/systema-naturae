import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

interface GbifCache {
  downloadedAt: string;
  speciesByFamily: Record<string, { gbifKey: number; species: Record<string, unknown>[] }>;
  familyKeyToName: Record<number, string>;
}

interface ColorTheme {
  appSlug: string;
  className: string;
  orderName: string;
  name: string;
  mainColor: string;
  lineageColors: Record<string, string>;
}

const args = process.argv.slice(2);
const [className, gbifClassName, classId, classKey, speciesCount] = args;

if (!className || !classId || !classKey) {
  console.error("Usage: npx tsx scripts/bootstrapClass.ts <ClassName> <GbifClassName> <CLASS_ID> <gbifKey> <speciesCount>");
  console.error("Example: npx tsx scripts/bootstrapClass.ts Hydrozoa Hydrozoa HYDROZOA 205 4545");
  process.exit(1);
}

// ── 1. Read cache ──
const cachePath = resolve(root, "portal", "data", `gbif-cache-${className.toLowerCase()}.json`);
if (!existsSync(cachePath)) {
  console.error(`Cache not found at ${cachePath}. Run cacheGbifData.ts first.`);
  process.exit(1);
}
const cache: GbifCache = JSON.parse(readFileSync(cachePath, "utf-8"));
console.log(`\n📦 Loaded cache: ${Object.keys(cache.speciesByFamily).length} families\n`);

// ── 2. Group families by order (skip families with no species) ──
const orders = new Map<string, { name: string; families: { name: string; count: number }[] }>();
for (const [famName, info] of Object.entries(cache.speciesByFamily)) {
  if (!info.species?.length) continue;
  const orderName = (info.species[0] as Record<string, unknown>).order as string || "Unknown";
  if (!orders.has(orderName)) orders.set(orderName, { name: orderName, families: [] });
  orders.get(orderName)!.families.push({ name: famName, count: info.species.length });
}
console.log(`📊 ${orders.size} orders, ${[...orders.values()].reduce((s, o) => s + o.families.length, 0)} families\n`);

// ── 3. Taxonomy JSON skeleton generation ──
function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

interface TaxonomyNode {
  id: string;
  name: string;
  rank: string;
  [key: string]: unknown;
}

function buildTaxonomyJson(): TaxonomyNode {
  const sortedOrders = [...orders.entries()].sort((a, b) => {
    const totalA = a[1].families.reduce((s, f) => s + f.count, 0);
    const totalB = b[1].families.reduce((s, f) => s + f.count, 0);
    return totalB - totalA;
  });

  return {
    id: classId,
    name: className,
    rank: "CLASS",
    commonName: `${className}`,
    speciesCount,
    children: sortedOrders.map(([, order]) => {
      const orderTotal = order.families.reduce((s, f) => s + f.count, 0);
      return {
        id: makeId(order.name, classId),
        name: order.name,
        rank: "ORDER",
        commonName: `${order.name}`,
        children: order.families.sort((a, b) => b.count - a.count).map(fam => ({
          id: makeId(fam.name, "FAM"),
          name: fam.name,
          rank: "FAMILY",
          commonName: `${fam.name}`,
          appSlug: fam.name.toLowerCase(),
          speciesCount: fam.count,
        })),
      };
    }),
  };
}

// ── 4. Color theme generation ──
function generateColorThemes(): ColorTheme[] {
  const palette = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
    "#06B6D4", "#D946EF", "#0EA5E9", "#22C55E", "#EAB308",
    "#A855F7", "#FB923C", "#2DD4BF", "#A3E635", "#38BDF8",
  ];
  let colorIdx = 1; // skip index 0 (reserved for class-level)

  const themes: ColorTheme[] = [];
  for (const [orderName, order] of orders) {
    for (const fam of order.families.sort((a, b) => b.count - a.count)) {
      const c = palette[colorIdx % palette.length];
      const lc = palette[(colorIdx + 5) % palette.length];
      colorIdx++;
      themes.push({
        appSlug: fam.name.toLowerCase(),
        className,
        orderName,
        name: fam.name,
        mainColor: c,
        lineageColors: { [fam.name.toLowerCase()]: lc },
      });
    }
  }
  return themes;
}

// ── 5. Create directory structures ──
function createDirectories() {
  for (const [orderName, order] of orders) {
    for (const fam of order.families) {
      const slug = fam.name.toLowerCase();
      const dirPath = resolve(root, className.toLowerCase(), orderName.toLowerCase(), slug, "src", "data");
      mkdirSync(dirPath, { recursive: true });
    }
  }
}

// ── 6. Output ──
const taxFragment = buildTaxonomyJson();
const colorThemes = generateColorThemes();

console.log("=== TAXONOMY JSON FRAGMENT ===\n");
console.log(JSON.stringify(taxFragment, null, 2));

console.log("\n=== COLOR THEME ENTRIES ===\n");
console.log(`// ${className} families`);
for (const t of colorThemes) {
  console.log(`const ${className.toLowerCase()}_${t.appSlug}: ColorTheme = { appSlug: "${t.appSlug}", className: "${t.className}", orderName: "${t.orderName}", name: "${t.name}", mainColor: "${t.mainColor}", lineageColors: { "${t.appSlug}": "${t.lineageColors[t.appSlug]}" } };`);
}

console.log(`\n// Register in COLOR_REGISTRY`);
for (const t of colorThemes) {
  console.log(`  "${t.appSlug}": ${className.toLowerCase()}_${t.appSlug},`);
}

console.log(`\n=== DIRECTORIES ===`);
createDirectories();
console.log(`Created ${[...orders.values()].reduce((s, o) => s + o.families.length, 0)} directory structures`);

console.log(`\n=== ORDERS SUMMARY ===`);
for (const [orderName, order] of [...orders.entries()].sort((a, b) => {
  const totalA = a[1].families.reduce((s, f) => s + f.count, 0);
  const totalB = b[1].families.reduce((s, f) => s + f.count, 0);
  return totalB - totalA;
})) {
  const total = order.families.reduce((s, f) => s + f.count, 0);
  console.log(`  ${orderName}: ${order.families.length} families, ${total} spp`);
  for (const fam of order.families.sort((a, b) => b.count - a.count)) {
    console.log(`    - ${fam.name}: ${fam.count} spp`);
  }
}
