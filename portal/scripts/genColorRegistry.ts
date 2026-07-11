/**
 * genColorRegistry.ts — generic per-family HSL ColorTheme generator for any kingdom.
 * Reads data/taxonomy-<kingdom>.json, writes src/colorRegistry<Kingdom>.ts.
 * Deterministic golden-angle hue distribution (mirrors Plantae/Fungi registries).
 *
 * Usage: npx tsx scripts/genColorRegistry.ts --kingdom Chromista [--base 200]
 */
import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

function arg(name: string, def = ""): string {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : def;
}

const KINGDOM = arg("kingdom");
if (!KINGDOM) { console.error("Usage: genColorRegistry.ts --kingdom <Name> [--base <hue>]"); process.exit(1); }
const KLOWER = KINGDOM.toLowerCase();
const CAP = KINGDOM.charAt(0).toUpperCase() + KINGDOM.slice(1).toLowerCase();
const TAX = resolve(portalRoot, `data/taxonomy-${KLOWER}.json`);
const OUT = resolve(portalRoot, `src/colorRegistry${CAP}.ts`);

const GOLDEN = 137.508;
const BASE_HUE = parseInt(arg("base", "200"), 10); // Chromista: aquatic blue-teal start

interface Node { rank: string; appSlug?: string; name: string; children?: Node[] }

const families: { slug: string; constName: string }[] = [];
const seen = new Set<string>();
function walk(n: Node) {
  if (n.rank === "FAMILY" && n.appSlug && !seen.has(n.appSlug)) {
    seen.add(n.appSlug);
    const safe = n.appSlug.replace(/[^a-z0-9]+/gi, "_").toUpperCase();
    families.push({ slug: n.appSlug, constName: (/^[0-9]/.test(safe) ? "F_" + safe : safe) + "_THEME" });
  }
  n.children?.forEach(walk);
}
walk(JSON.parse(readFileSync(TAX, "utf-8")) as Node);

const lines: string[] = [`import type { ColorTheme } from "@shared/types";`, ``];
families.forEach((f, i) => {
  const hue = (BASE_HUE + i * GOLDEN) % 360;
  const treeHue = (hue + 30) % 360;
  lines.push(
    `const ${f.constName}: ColorTheme = {"accent":"hsl(${hue}, 55%, 40%)","bg":"hsl(${hue}, 25%, 92%)","bgAlt":"hsl(${hue}, 20%, 96%)","border":"hsl(${hue}, 30%, 70%)","familyTree":"hsl(${treeHue}, 40%, 50%)","nodeFill":"hsl(${hue}, 35%, 70%)","nodeStroke":"hsl(${hue}, 50%, 35%)", subfamilyColors: {}, lineageColors: {}, breedGroupColor: "#888", hybridColor: "#888" };`
  );
});
lines.push(``, `export const COLOR_REGISTRY: Record<string, ColorTheme> = {`);
families.forEach(f => lines.push(`  "${f.slug}": ${f.constName},`));
lines.push(`};`, ``);

writeFileSync(OUT, lines.join("\n"));
console.log(`✅ Wrote ${OUT} with ${families.length} family themes`);
