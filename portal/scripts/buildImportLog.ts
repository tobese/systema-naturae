import { readFileSync, writeFileSync, existsSync, statSync } from "fs";
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

  try {
    const output = execSync(
      `git log --reverse --name-only --format="DATE:%aI %s"`,
      { cwd: root, encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 }
    );

    let currentDate = "";
    let currentMsg = "";

    for (const line of output.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith("DATE:")) {
        const parts = trimmed.slice(5).split(" ");
        currentDate = parts[0];
        currentMsg = parts.slice(1).join(" ");
        continue;
      }

      // Match family data files like standard sub-apps or root tardigrada
      if (trimmed.endsWith(".json") && trimmed.includes("/src/data/")) {
        const match = trimmed.match(/\/src\/data\/([^/]+)\.json$/);
        if (match) {
          const slug = match[1];
          if (!map.has(slug)) {
            map.set(slug, { date: currentDate, message: currentMsg.replace(/"/g, "'") });
          }
        }
      }
    }
  } catch (e) {
    console.error("Error fetching git log:", e);
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
      if (Array.isArray(node.speciesList)) {
        count += node.speciesList.length;
      }
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

  // For untracked families, use file mtime so uncommitted data gets accurate dates
  const tracked = new Set(firstCommits.keys());
  for (const slug of allSlugs) {
    if (!tracked.has(slug)) {
      const fp = familyPaths.get(slug);
      if (fp) {
        try {
          const mtime = statSync(fp).mtime.toISOString().slice(0, 10);
          slugDays.set(slug, mtime);
        } catch {
          slugDays.set(slug, "2026-06-14");
        }
      } else {
        slugDays.set(slug, "2026-06-14");
      }
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
  const autoDays = new Set<string>();

  // Read existing import-log to preserve manual entries
  const importLogPath = resolve(portalRoot, "data/import-log.json");
  let existingLog: ImportEvent[] = [];
  if (existsSync(importLogPath)) {
    try {
      existingLog = JSON.parse(readFileSync(importLogPath, "utf-8"));
    } catch { /* ignore */ }
  }

  // Identify entries that git/mtime can derive — they get fresh data
  // Entries with message or commit text are "manual" and get preserved
  const manualEntries = new Map<string, ImportEvent>();
  for (const entry of existingLog) {
    if (entry.message || entry.commit) {
      manualEntries.set(entry.date, entry);
    }
  }

  const events: ImportEvent[] = [];

  for (const day of sortedDays) {
    autoDays.add(day);
    const fams = dayGroups.get(day)!.sort();
    const speciesAdded = fams.reduce((sum, slug) => sum + (speciesCounts.get(slug) ?? 0), 0);
    speciesRunning += speciesAdded;

    const manual = manualEntries.get(day);
    if (manual) {
      // Preserve manual message/commit, merge families
      events.push({
        date: day,
        commit: manual.commit || "",
        message: manual.message || "",
        families: [...new Set([...manual.families, ...fams])].sort(),
        speciesAdded,
        speciesRunning,
        nodes: totalNodes,
      });
      manualEntries.delete(day);
    } else {
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
  }

  // Append any manual entries for dates not covered by auto
  for (const [day, entry] of manualEntries) {
    events.push({
      date: day,
      commit: entry.commit || "",
      message: entry.message || "",
      families: entry.families,
      speciesAdded: entry.speciesAdded,
      speciesRunning: entry.speciesRunning,
      nodes: entry.nodes || totalNodes,
    });
  }

  // Re-sort by date
  events.sort((a, b) => a.date.localeCompare(b.date));

  // Fix speciesRunning for the appended manual entries (they break sequential sum)
  // Recalculate running totals sequentially
  let runningFix = 0;
  for (const ev of events) {
    runningFix += ev.speciesAdded;
    ev.speciesRunning = runningFix;
  }

  writeFileSync(importLogPath, JSON.stringify(events, null, 2) + "\n");
  console.log(`  Wrote ${events.length} events to data/import-log.json`);
  console.log(`  ${allSlugs.length} families tracked, ${runningFix} total species`);
}

main();
