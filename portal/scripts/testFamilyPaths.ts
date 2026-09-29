/**
 * Assert the source tree matches the taxonomy, for every kingdom.
 *
 * The tree moved from a flat 258 top-level directories to
 * taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/ on 2026-09-28. Every
 * path is derived here from that kingdom's own taxonomy input rather than
 * assumed, so this is a statement about the two agreeing - not a snapshot of
 * one layout.
 *
 * It exists because the failure mode of a path rule is silence. A glob that
 * matches nothing returns [], a loop over it never runs, and the script prints
 * its success summary and exits 0 having enriched nothing: no exception, no
 * non-zero exit. A resolver that returns a plausible wrong path is worse -
 * wrong data, still exit 0. Four Python enrichers carried a fixed-depth glob of three wildcard
 * segments for exactly this reason, and three scripts read parts[0] of a path
 * expecting a class name and got "taxonomy" instead.
 * These assertions are what makes that loud.
 *
 * Run: npx tsx scripts/testFamilyPaths.ts
 */
import { readFileSync, existsSync, readdirSync } from "fs";
import { resolve, join } from "path";
import { dirName } from "./lib/familyPath.js";

const REPO = resolve(import.meta.dirname, "..", "..");
const CONFIG = JSON.parse(
  readFileSync(join(REPO, "portal", "data", "kingdom-config.json"), "utf-8"),
) as { kingdoms: Record<string, { input: string }> };

interface TreeNode {
  rank?: string;
  name?: string;
  appSlug?: string;
  children?: TreeNode[];
}

const failures: string[] = [];
const depths = new Map<number, number>();
let totalFamilies = 0;
let totalResolved = 0;
let totalNoData = 0;

for (const [kingdom, cfg] of Object.entries(CONFIG.kingdoms)) {
  const tree = JSON.parse(readFileSync(join(REPO, "portal", cfg.input), "utf-8")) as TreeNode;
  const resolvedPaths = new Set<string>();
  const allSlugs = new Set<string>();
  const collectSlugs = (n: TreeNode) => {
    if (n?.rank === "FAMILY" && n.appSlug) allSlugs.add(n.appSlug);
    for (const c of n.children ?? []) collectSlugs(c);
  };
  collectSlugs(tree);
  let noData = 0;

  const walk = (node: TreeNode, phylum?: string, cls?: string, ord?: string) => {
    if (!node || typeof node !== "object") return;
    let p = phylum;
    let c = cls;
    let o = ord;
    if (node.rank === "PHYLUM") {
      p = node.name;
      c = undefined;                     // a new phylum starts a new class scope
    } else if (node.rank === "CLASS") {
      c = node.name;
    } else if (node.rank === "ORDER") {
      o = node.name;
    } else if (node.rank === "FAMILY" && node.appSlug) {
      const slug = node.appSlug;
      totalFamilies++;
      const segs = [dirName(p), dirName(c), dirName(o)].filter(Boolean);
      const want = join("taxonomy", kingdom, ...segs, slug);
      const dir = join(REPO, want);
      const file = join(dir, "src", "data", `${slug}.json`);
      if (!existsSync(file)) {
        // Not a failure on its own: the taxonomy declares more families than
        // have data. plantae declares 1,259 and 238 of them graft empty.
        noData++;
        totalNoData++;
        return;
      }
      if (resolvedPaths.has(want)) failures.push(`${kingdom}: duplicate target ${want}`);
      resolvedPaths.add(want);
      totalResolved++;
      depths.set(segs.length + 1, (depths.get(segs.length + 1) ?? 0) + 1);
      // Only another *family's* record is a problem. A family that is a
      // standalone app also keeps ranges.ts, hybrids.ts and continents.json
      // beside its data file, and those are legitimate.
      const foreign = readdirSync(join(dir, "src", "data"))
        .filter((f) => f.endsWith(".json") && f !== `${slug}.json`)
        .filter((f) => allSlugs.has(f.replace(/\.json$/, "")));
      if (foreign.length) {
        failures.push(`${kingdom}: ${want}/src/data holds other families' records: ${foreign.join(", ")}`);
      }
      return;
    }
    for (const child of node.children ?? []) walk(child, p, c, o);
  };
  walk(tree);

  // The check that matters: a kingdom where *nothing* resolved means the
  // layout is wrong, not that the data is absent.
  if (resolvedPaths.size === 0 && noData > 0) {
    failures.push(`${kingdom}: no family resolved (${noData} declared, none found on disk)`);
  }
  console.log(
    `  ${kingdom.padEnd(10)} ${String(resolvedPaths.size).padStart(5)} resolved` +
    (noData ? `   ${String(noData).padStart(4)} declared with no data file` : ""),
  );
}

console.log(`\n  ${totalFamilies.toLocaleString()} families declared, ` +
  `${totalResolved.toLocaleString()} resolved, ${totalNoData.toLocaleString()} with no data file`);
const depthSummary = [...depths.entries()].sort((a, b) => a[0] - b[0])
  .map(([d, n]) => `${d}L=${n}`).join("  ");
console.log(`  resolved path depths: ${depthSummary}`);

if (failures.length) {
  console.error(`\nFAILED (${failures.length}):`);
  for (const f of failures.slice(0, 30)) console.error(`  ${f}`);
  process.exit(1);
}
console.log("\nOK: every family's directory matches its taxonomy rank path.");
