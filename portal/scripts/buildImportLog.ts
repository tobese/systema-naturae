import { readFileSync, writeFileSync, existsSync } from "fs";
import { execSync } from "child_process";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

interface ImportEvent {
  date: string;
  commit: string;
  message: string;
  families: string[];
  speciesAdded: number;
  speciesRunning: number;
  nodes: number;
}

/** Get the first commit that introduced each family data file */
function getFamilyFirstCommits(): Map<string, { commit: string; date: string; message: string }> {
  const map = new Map<string, { commit: string; date: string; message: string }>();
  const log = execSync(
    `git log --all --reverse --diff-filter=A --name-only --format="COMMIT %H %aI %s" -- '*/src/data/*.json'`,
    { cwd: root, encoding: "utf-8" },
  );

  let currentCommit = "";
  let currentDate = "";
  let currentMessage = "";
  for (const line of log.split("\n")) {
    if (line.startsWith("COMMIT ")) {
      const parts = line.slice(7).split(" ");
      currentCommit = parts[0];
      currentDate = parts[1];
      currentMessage = parts.slice(2).join(" ").replace(/"/g, "'");
    } else if (line.includes("/src/data/")) {
      const match = line.match(/\/([^/]+)\/src\/data\//);
      if (match) {
        const appSlug = match[1];
        if (!map.has(appSlug)) {
          map.set(appSlug, { commit: currentCommit, date: currentDate, message: currentMessage });
        }
      }
    }
  }
  return map;
}

/** Build a map of appSlug → file path for all family data files */
function buildFamilyPathMap(): Map<string, string> {
  const map = new Map<string, string>();
  const result = execSync(
    `find ${root} -name "*.json" -path "*/src/data/*" -type f -not -path "*/node_modules/*"`,
    { encoding: "utf-8" },
  );
  for (const path of result.trim().split("\n")) {
    const match = path.match(/\/([^/]+)\/src\/data\/\1\.json$/);
    if (match) map.set(match[1], path);
  }
  return map;
}

/** Count species in a family data file */
function countSpecies(path: string): number {
  try {
    const data = JSON.parse(readFileSync(path, "utf-8"));
    let count = 0;
    function walk(node: Record<string, unknown>) {
      if (node.rank === "SPECIES") count++;
      for (const child of (node.children ?? []) as Record<string, unknown>[]) walk(child);
    }
    walk(data);
    return count;
  } catch {
    return 0;
  }
}

/** Count total nodes in the current unified taxonomy */
function countNodes(): number {
  const path = resolve(portalRoot, "data/unified-taxonomy.json");
  if (!existsSync(path)) return 0;
  try {
    const data = JSON.parse(readFileSync(path, "utf-8"));
    let count = 0;
    function walk(node: Record<string, unknown>) {
      count++;
      for (const child of (node.children ?? []) as Record<string, unknown>[]) walk(child);
    }
    walk(data);
    return count;
  } catch {
    return 0;
  }
}

/** Get all unique appSlugs from the current taxonomy */
function getAllAppSlugs(): string[] {
  const path = resolve(portalRoot, "data/taxonomy.json");
  if (!existsSync(path)) return [];
  try {
    const data = JSON.parse(readFileSync(path, "utf-8"));
    const slugs: string[] = [];
    function walk(node: Record<string, unknown>) {
      if (node.rank === "FAMILY" && node.appSlug) {
        slugs.push(node.appSlug as string);
      }
      for (const child of (node.children ?? []) as Record<string, unknown>[]) walk(child);
    }
    walk(data);
    return slugs;
  } catch {
    return [];
  }
}

function main() {
  console.log("Building import log…");

  const familyPaths = buildFamilyPathMap();
  const firstCommits = getFamilyFirstCommits();
  const allSlugs = getAllAppSlugs();
  const totalNodes = countNodes();

  // Group family data files by their first commit
  const commitGroups = new Map<string, { commit: string; date: string; message: string; families: string[] }>();

  for (const [slug, info] of firstCommits) {
    if (!allSlugs.includes(slug)) continue; // skip families no longer in taxonomy
    if (!commitGroups.has(info.commit)) {
      commitGroups.set(info.commit, { ...info, families: [] });
    }
    commitGroups.get(info.commit)!.families.push(slug);
  }

  // For untracked families, try to find their first mention in git history
  const tracked = new Set(firstCommits.keys());
  const untracked = allSlugs.filter(s => !tracked.has(s));
  if (untracked.length > 0) {
    console.log(`  ${untracked.length} untracked families — finding earliest git mention…`);
    // Check if each untracked slug ever appears in any commit
    for (const slug of untracked) {
      try {
        const result = execSync(
          `git log --all --oneline --diff-filter=A --format="%H %aI" -- '*${slug}*'`,
          { cwd: root, encoding: "utf-8", timeout: 5000 },
        ).trim();
        if (result) {
          const [hash, date] = result.split("\n")[0].split(" ");
          // Check if this commit already has a group
          if (!commitGroups.has(hash)) {
            commitGroups.set(hash, { commit: hash, date: date || "2026-06-14T10:00:00", message: "", families: [] });
          }
          commitGroups.get(hash)!.families.push(slug);
        } else {
          // Fallback: use earliest repo commit
          const key = "__initial__";
          if (!commitGroups.has(key)) {
            commitGroups.set(key, {
              commit: "initial",
              date: "2026-06-14T10:00:00",
              message: "Initial families — from early portal commits",
              families: [],
            });
          }
          commitGroups.get(key)!.families.push(slug);
        }
      } catch {
        const key = "__initial__";
        if (!commitGroups.has(key)) {
          commitGroups.set(key, {
            commit: "initial", date: "2026-06-14T10:00:00",
            message: "Initial families — from early portal commits",
            families: [],
          });
        }
        commitGroups.get(key)!.families.push(slug);
      }
    }
  }

  // Sort by date
  const sorted = [...commitGroups.entries()]
    .filter(([_, g]) => g.families.length > 0)
    .sort((a, b) => a[1].date.localeCompare(b[1].date));

  // Compute running totals
  let speciesRunning = 0;
  const events: ImportEvent[] = [];

  // Precompute species counts for all slugs
  const speciesCounts = new Map<string, number>();
  for (const [slug, p] of familyPaths) {
    speciesCounts.set(slug, countSpecies(p));
  }

  for (const [, group] of sorted) {
    const speciesAdded = group.families.reduce((sum, slug) => sum + (speciesCounts.get(slug) ?? 0), 0);
    speciesRunning += speciesAdded;
    events.push({
      date: group.date,
      commit: group.commit,
      message: group.message,
      families: group.families.sort(),
      speciesAdded,
      speciesRunning,
      nodes: totalNodes, // current total; retroactive approximation
    });
  }

  const outPath = resolve(portalRoot, "data/import-log.json");
  writeFileSync(outPath, JSON.stringify(events, null, 2));
  console.log(`  Wrote ${events.length} events to data/import-log.json`);
  console.log(`  ${allSlugs.length} families tracked, ${speciesRunning} total species`);
}

main();
