import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const TAX = JSON.parse(readFileSync(resolve(root, "portal", "data", "taxonomy.json"), "utf-8"));
const COLOR_PATH = resolve(root, "portal", "src", "colorRegistry.ts");
const colorTs = readFileSync(COLOR_PATH, "utf-8");

// Get existing slugs from colorRegistry
const existingSlugs = new Set<string>();
for (const line of colorTs.split("\n")) {
  const m = line.match(/^\s+"([^"]+)":\s+\w+/);
  if (m) existingSlugs.add(m[1]);
}

const palette = [
  "#3B82F6","#EF4444","#10B981","#F59E0B","#8B5CF6",
  "#EC4899","#14B8A6","#F97316","#6366F1","#84CC16",
  "#06B6D4","#D946EF","#0EA5E9","#22C55E","#EAB308",
  "#A855F7","#FB923C","#2DD4BF","#A3E635","#38BDF8",
];

function findClass(n: any, id: string): any {
  if (n.id === id) return n;
  for (const c of n.children ?? []) {
    const found = findClass(c, id);
    if (found) return found;
  }
  return null;
}

const classNode = findClass(TAX, "CEPHALOPODA");
let idx = 0;
const themeLines: string[] = [];
const registerLines: string[] = [];

for (const order of classNode.children) {
  for (const fam of order.children) {
    const slug = fam.appSlug;
    if (existingSlugs.has(slug)) continue;
    const c = palette[idx % palette.length];
    const lc = palette[(idx + 5) % palette.length];
    idx++;
    const constName = `cephalopoda_${slug}`;
    themeLines.push(`const ${constName}: ColorTheme = { subfamilyColors: {}, breedGroupColor: "${c}", hybridColor: "${lc}", appSlug: "${slug}", className: "Cephalopoda", orderName: "${order.name}", name: "${fam.name}", mainColor: "${c}", lineageColors: { "${slug}": "${lc}" } };`);
    registerLines.push(`  "${slug}": ${constName},`);
  }
}

if (themeLines.length === 0) {
  console.log("All families already have color themes.");
  process.exit(0);
}

const registryMarker = "export const COLOR_REGISTRY: Record<string, ColorTheme> = {";
const themeHeader = `\n// ── Cephalopoda (${classNode.children.length} orders) ──\n`;
const themeInsertion = themeHeader + themeLines.join("\n") + "\n\n";

const beforeRegistry = colorTs.substring(0, colorTs.lastIndexOf(registryMarker));
const afterRegistry = colorTs.substring(colorTs.lastIndexOf(registryMarker));
const registryEnd = afterRegistry.indexOf("};", registryMarker.length);
const registryBody = afterRegistry.substring(registryMarker.length, registryEnd);
const updatedRegistry = afterRegistry.substring(0, registryMarker.length) + registryBody + "\n" + registerLines.join("\n") + afterRegistry.substring(registryEnd);

writeFileSync(COLOR_PATH, beforeRegistry + themeInsertion + updatedRegistry);
console.log(`Added ${themeLines.length} color themes to colorRegistry.ts`);
