import { execSync } from "child_process";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

const PORTAL = resolve(import.meta.dirname, "..");
// Defaults to animalia, like buildData.ts. Without it this read the legacy flat
// data/unified-taxonomy.json while the build wrote data/kingdoms/animalia/ - a
// 375MB file last written in July, before the per-kingdom restructure - so the
// node counts could never agree and this reported a mismatch on a good build.
const KINGDOM = process.env.SN_KINGDOM || "animalia";
const UNIFIED = resolve(PORTAL, `data/kingdoms/${KINGDOM}/unified-taxonomy.json`);
/**
 * The smallest tree this kingdom may legitimately produce: the skeleton the
 * build just wrote, counted the same way countNodes() counts the monolith -
 * `children` only. The skeleton's rankCounts would not do, because they sum
 * the compressed speciesList members that countNodes never visits (593,254
 * against 194,596 for animalia). The build always writes the skeleton, so this
 * needs no per-kingdom table and stays right as the data changes.
 */
function skeletonNodes(): number {
  const p = resolve(PORTAL, "public", "data", "kingdoms", KINGDOM, "unified-taxonomy-skeleton.json");
  if (!existsSync(p)) return 0;
  const sk = JSON.parse(readFileSync(p, "utf-8")) as TreeNode;
  return countNodes(sk);
}

interface TreeNode {
  id?: string;
  name?: string;
  rank?: string;
  familySlug?: string;
  children?: TreeNode[];
}

function countNodes(node: TreeNode): number {
  let n = 1;
  if (node.children) {
    for (const c of node.children) {
      n += countNodes(c);
    }
  }
  return n;
}

function collectFamilySlugs(node: TreeNode, slugs: Set<string>): void {
  if (node.familySlug) slugs.add(node.familySlug);
  if (node.children) {
    for (const c of node.children) {
      collectFamilySlugs(c, slugs);
    }
  }
}

function main() {
  const checkSlugs = process.argv.slice(2);

  // 1. Run build
  console.log(`⏳ Building unified taxonomy${KINGDOM ? ` for ${KINGDOM}` : ""}...`);
  const start = Date.now();
  // The monolith is opt-in, and validating it is this script's entire purpose,
  // so it asks for it explicitly rather than assuming every build writes it.
  const env = {
    ...process.env,
    ...(KINGDOM ? { SN_KINGDOM: KINGDOM } : {}),
    SN_BUILD_UNIFIED: "1",
  };
  const out = execSync("sh scripts/buildData.sh", {
    cwd: PORTAL,
    encoding: "utf-8",
    timeout: 60000,
    env,
  });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  // 2. Check for warnings
  const warnings = out.match(/Warning:/g);
  if (warnings && warnings.length > 0) {
    // Extract which files are missing
    const missing = (out.match(/could not load ([^:]+)/g) || []).map((m: string) =>
      m.replace("could not load ", "")
    );
    console.error(`⚠  ${warnings.length} build warning(s) — missing data files:`);
    for (const f of missing) {
      console.error(`   ${f}`);
    }
  }

  // 3. Parse the build's node counts. countNodes() below walks `children` only
  //    and never descends into `speciesList`, so it must be compared against
  //    "physical nodes" - "total nodes represented" includes the compressed
  //    speciesList members and would always disagree.
  const nodeMatch = out.match(/Done\. (\d+) physical nodes/);
  if (!nodeMatch) {
    console.error("❌ Build failed or output format unexpected");
    console.error(out);
    process.exit(1);
  }
  const totalNodes = parseInt(nodeMatch[1], 10);

  // 4. Validate unified JSON
  if (!existsSync(UNIFIED)) {
    console.error(`❌ ${UNIFIED} not found after build`);
    process.exit(1);
  }

  let tax: TreeNode;
  try {
    tax = JSON.parse(readFileSync(UNIFIED, "utf-8"));
  } catch {
    console.error("❌ unified-taxonomy.json is not valid JSON");
    process.exit(1);
  }

  // 5. Verify node count
  const actualNodes = countNodes(tax);
  if (actualNodes !== totalNodes) {
    console.error(
      `❌ Node count mismatch: tree walk=${actualNodes}, build output=${totalNodes}`
    );
    process.exit(1);
  }

  // Read after the build, not at module load: on a clean checkout the skeleton
  // does not exist yet and a floor computed then would be a vacuous zero.
  const MIN_NODES = skeletonNodes();
  if (actualNodes < MIN_NODES) {
    console.error(
      `❌ Node count ${actualNodes} below minimum ${MIN_NODES} for kingdom ${KINGDOM}.` +
      ` The skeleton declares ${skeletonNodes()}, which is the real floor: a fixed` +
      ` number cannot be right for six kingdoms spanning 194,596 nodes down to 726.`
    );
    process.exit(1);
  }

  // 6. Check requested family slugs exist
  const allSlugs: Set<string> = new Set();
  collectFamilySlugs(tax, allSlugs);

  for (const slug of checkSlugs) {
    if (!allSlugs.has(slug)) {
      console.error(`❌ Family "${slug}" not found in unified taxonomy`);
      process.exit(1);
    }
  }

  // 7. Report
  const warnText = warnings?.length ? `, ${warnings.length} warnings` : "";
  console.log(`✅ Build OK — ${actualNodes} nodes in ${elapsed}s${warnText}`);
}

main();
