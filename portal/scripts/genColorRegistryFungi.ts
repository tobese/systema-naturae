/**
 * genColorRegistryFungi.ts
 *
 * Generates portal/src/colorRegistryFungi.ts from data/taxonomy-fungi.json.
 * One deterministic HSL ColorTheme per family (golden-angle hue distribution),
 * mirroring the auto-generated Plantae registry format.
 *
 * Usage: npx tsx scripts/genColorRegistryFungi.ts
 */
import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");
const TAX = resolve(portalRoot, "data/taxonomy-fungi.json");
const OUT = resolve(portalRoot, "src/colorRegistryFungi.ts");

const GOLDEN = 137.508;
const BASE_HUE = 25; // earthy starting hue, offset from Plantae's 30

interface Node { rank: string; appSlug?: string; name: string; children?: Node[] }

const families: { slug: string; constName: string }[] = [];
const seen = new Set<string>();

function walk(n: Node) {
  if (n.rank === "FAMILY" && n.appSlug && !seen.has(n.appSlug)) {
    seen.add(n.appSlug);
    families.push({
      slug: n.appSlug,
      constName: n.appSlug.replace(/[^a-z0-9]+/gi, "_").toUpperCase() + "_THEME",
    });
  }
  n.children?.forEach(walk);
}

const tax = JSON.parse(readFileSync(TAX, "utf-8")) as Node;
walk(tax);

const lines: string[] = [];
lines.push(`import type { ColorTheme } from "@shared/types";`);
lines.push(``);

families.forEach((f, i) => {
  const hue = (BASE_HUE + i * GOLDEN) % 360;
  const treeHue = (hue + 30) % 360;
  const theme = {
    accent: `hsl(${hue}, 55%, 40%)`,
    bg: `hsl(${hue}, 25%, 92%)`,
    bgAlt: `hsl(${hue}, 20%, 96%)`,
    border: `hsl(${hue}, 30%, 70%)`,
    familyTree: `hsl(${treeHue}, 40%, 50%)`,
    nodeFill: `hsl(${hue}, 35%, 70%)`,
    nodeStroke: `hsl(${hue}, 50%, 35%)`,
  };
  lines.push(
    `const ${f.constName}: ColorTheme = {"accent":"${theme.accent}","bg":"${theme.bg}","bgAlt":"${theme.bgAlt}","border":"${theme.border}","familyTree":"${theme.familyTree}","nodeFill":"${theme.nodeFill}","nodeStroke":"${theme.nodeStroke}", subfamilyColors: {}, lineageColors: {}, breedGroupColor: "#888", hybridColor: "#888" };`
  );
});

lines.push(``);
lines.push(`export const COLOR_REGISTRY: Record<string, ColorTheme> = {`);
families.forEach(f => lines.push(`  "${f.slug}": ${f.constName},`));
lines.push(`};`);
lines.push(``);

writeFileSync(OUT, lines.join("\n"));
console.log(`✅ Wrote ${OUT} with ${families.length} family themes`);
