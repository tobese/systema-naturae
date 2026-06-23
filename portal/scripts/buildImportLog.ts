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

/** Get each family's earliest git commit by following renames */
function getFamilyFirstCommits(): Map<string, { date: string; message: string }> {
  const map = new Map<string, { date: string; message: string }>();
  const familyPaths = buildFamilyPathMap();

  for (const [slug, path] of familyPaths) {
    try {
      const result = execSync(
        `git log --all --follow --format="%aI %s" -- "${path}"`,
        { cwd: root, encoding: "utf-8", timeout: 3000 },
      ).trim();
      if (result) {
        const firstLine = result.split("\n").pop() || ""; // last = oldest (reverse order not used)
        // Actually git log goes most-recent-first. We need the LAST line for the oldest.
        // With --follow, results are most-recent-first. We want the final one.
        // Actually git log without --reverse goes most-recent-first.
        // Let's just use the first line (which IS the earliest since we don't reverse)
        // Wait no — without --reverse, the FIRST line is the MOST recent.
        // We want the LAST line (oldest).
        // Actually with --follow, we want the OLDEST commit.
        // Let's use --reverse.
        const revResult = execSync(
          `git log --all --follow --reverse --format="%aI %s" -- "${path}"`,
          { cwd: root, encoding: "utf-8", timeout: 5000 },
        ).trim();
        if (revResult) {
          const firstLine = revResult.split("\n")[0];
          const date = firstLine.split(" ")[0];
          const msg = firstLine.slice(date.length + 1);
          map.set(slug, { date, message: msg.replace(/"/g, "'") });
        }
      }
    } catch {
      // skip
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
  const allSlugs = getAllAppSlugs();
  const totalNodes = countNodes();

  // Precompute species counts
  const speciesCounts = new Map<string, number>();
  for (const [slug, p] of familyPaths) {
    speciesCounts.set(slug, countSpecies(p));
  }

  // Get first-commit dates for each family
  const firstCommits = getFamilyFirstCommits();

  // Map each family slug → its first commit date (YYYY-MM-DD)
  const slugDays = new Map<string, string>();

  for (const [slug, info] of firstCommits) {
    if (!allSlugs.includes(slug)) continue;
    slugDays.set(slug, info.date.slice(0, 10));
  }

  // For untracked families, use earliest repo date
  const tracked = new Set(firstCommits.keys());
  for (const slug of allSlugs) {
    if (!tracked.has(slug)) {
      slugDays.set(slug, "2026-06-14");
    }
  }

  // Group by day
  const dayGroups = new Map<string, string[]>();
  for (const [slug, day] of slugDays) {
    if (!dayGroups.has(day)) dayGroups.set(day, []);
    dayGroups.get(day)!.push(slug);
  }

  // Sort days and compute running totals
  const sortedDays = [...dayGroups.keys()].sort();
  let speciesRunning = 0;
  const events: ImportEvent[] = [];

  for (const day of sortedDays) {
    const fams = dayGroups.get(day)!.sort();
    const speciesAdded = fams.reduce((sum, slug) => sum + (speciesCounts.get(slug) ?? 0), 0);
    speciesRunning += speciesAdded;
    events.push({
      date: day,
      commit: "",
      message: "",
      families: fams,
      speciesAdded,
      speciesRunning,
      nodes: totalNodes,
    });
  }

  const outPath = resolve(portalRoot, "data/import-log.json");
  writeFileSync(outPath, JSON.stringify(events, null, 2));
  console.log(`  Wrote ${events.length} events to data/import-log.json`);
  console.log(`  ${allSlugs.length} families tracked, ${speciesRunning} total species`);
}

main();
