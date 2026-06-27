/**
 * mergeWikiInfoboxes — fold image / range_map / IUCN status from the
 * offline Wikipedia SQLite dump into shared/data/wiki-images.json.
 *
 * The SQLite DB is produced by scripts/buildWikipediaDb.py (parses the
 * enwiki multistream XML dump). Its `infobox_json` column holds parsed
 * species-box fields: image, image2, range_map, range_map2, status,
 * status_system. We merge those into the existing cache so the runtime
 * hook has more portraits / range tabs / IUCN badges without re-querying
 * Wikidata.
 *
 * Conflict policy: prefer existing Wikidata-cached values — they are
 * newer (Wikidata updates faster than per-article infoboxes) — and only
 * fill in MISSING fields from the infobox. The SQLite status code is
 * already a short IUCN code (LC/EN/VU/...), no QID mapping needed.
 *
 * We also backfill `qid: ""` placeholder entries (binomials that
 * Wikidata didn't know about) if the infobox has useful data.
 *
 * Usage:
 *   npx tsx scripts/mergeWikiInfoboxes.ts            # full run
 *   npx tsx scripts/mergeWikiInfoboxes.ts --dry-run   # report only
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { spawnSync } from "child_process";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const CACHE_PATH = join(ROOT, "shared", "data", "wiki-images.json");
const SQLITE_DB = "/Volumes/WikiDump/wiki-pages.sqlite";
const IUCN_CODES = new Set(["EX", "EW", "CR", "EN", "VU", "NT", "LC", "DD", "NE"]);

interface CacheEntry {
  qid: string;
  image?: string;
  rangeMaps?: string[];
  commonsCat?: string;
  iucnStatus?: string;
  fetchedAt: string;
}

interface InfoboxRow {
  title: string;
  infobox_json: string | null;
  extract: string | null;
}

function readInfoboxRows(): Map<string, InfoboxRow> {
  if (!existsSync(SQLITE_DB)) {
    console.error(`SQLite DB not found at ${SQLITE_DB}`);
    process.exit(1);
  }
  const script = `
import json, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
out = {}
for title, info, extract in db.execute(
    "SELECT title, infobox_json, extract FROM pages WHERE infobox_json IS NOT NULL OR extract IS NOT NULL"
):
    out[title] = {"title": title, "infobox_json": info, "extract": extract}
print(json.dumps(out))
`;
  const res = spawnSync("python3", ["-c", script, SQLITE_DB], {
    encoding: "utf-8",
    maxBuffer: 256 * 1024 * 1024,
  });
  if (res.status !== 0 || !res.stdout.trim()) {
    console.error("sqlite read failed:", res.stderr);
    process.exit(1);
  }
  const rows = JSON.parse(res.stdout.trim()) as Record<string, InfoboxRow>;
  return new Map(Object.entries(rows));
}

function loadCache(): Record<string, CacheEntry> {
  if (!existsSync(CACHE_PATH)) return {};
  try {
    return JSON.parse(readFileSync(CACHE_PATH, "utf-8")) as Record<string, CacheEntry>;
  } catch {
    return {};
  }
}

function saveCache(cache: Record<string, CacheEntry>) {
  writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2) + "\n");
}

function main() {
  const dry = process.argv.includes("--dry-run");
  console.log("Reading infobox rows from SQLite…");
  const rows = readInfoboxRows();
  console.log(`  ${rows.size.toLocaleString()} pages with infobox/extract`);

  const cache = loadCache();
  const cachedCount = Object.keys(cache).length;
  console.log(`  ${cachedCount.toLocaleString()} entries in wiki-images.json`);

  let filledImage = 0;
  let filledRange = 0;
  let filledStatus = 0;
  let placeholderPromoted = 0;
  let touched = 0;
  const now = new Date().toISOString();

  for (const [title, row] of rows) {
    let info: Record<string, string> | null = null;
    try {
      if (row.infobox_json) info = JSON.parse(row.infobox_json);
    } catch {
      continue;
    }
    if (!info) continue;

    let entry = cache[title];
    if (!entry) {
      // Optional: skip binomials we never asked Wikidata about, to avoid
      // creating entries for names that aren't in any family JSON. The
      // hook just returns null for unknown keys, so harmless either way.
      // We add for completeness — title is a binomial by construction.
      entry = { qid: "", fetchedAt: now };
      cache[title] = entry;
    }

    let changed = false;

    // Image: prefer first unused image field; never overwrite Wikidata.
    if (!entry.image) {
      const img = info.image || info.image2;
      if (img && img.trim()) {
        entry.image = img.trim();
        filledImage++;
        changed = true;
      }
    }

    // Range maps: append any infobox range fields not already present.
    if (!entry.rangeMaps || entry.rangeMaps.length === 0) {
      const maps = [info.range_map, info.range_map2].filter(
        (m): m is string => !!m && m.trim().length > 0
      );
      if (maps.length > 0) {
        const dedup = maps.filter(
          (m) => !entry.rangeMaps?.includes(m)
        );
        if (dedup.length > 0) {
          entry.rangeMaps = [...(entry.rangeMaps ?? []), ...dedup];
          filledRange += dedup.length;
          changed = true;
        }
      }
    }

    // IUCN status: only accept recognized short codes.
    if (!entry.iucnStatus) {
      const st = (info.status || "").trim().toUpperCase();
      if (IUCN_CODES.has(st)) {
        entry.iucnStatus = st;
        filledStatus++;
        changed = true;
      }
    }

    // Promote entries that had qid:"" but now have useful fields. The
    // runtime hook returns null for qid:"" entries, so we need to flip
    // qid to a marker that signals "we have data". We reuse empty qid
    // but the hook checks for any useful field — let's verify:
    //   useWikiImages: `if (!entry || !entry.qid) return null;`
    // So qid:"" makes the entry useless to the hook. Set a local marker
    // by writing qid:"WIKIDATA_NONE" so the hook picks it up. We avoid
    // faking a real QID — this signals "Wikipedia-only, no Wikidata"
    // and is stable against re-runs.
    if (entry.qid === "" && (entry.image || (entry.rangeMaps && entry.rangeMaps.length > 0) || entry.iucnStatus)) {
      entry.qid = "WIKIDATA_NONE";
      placeholderPromoted++;
      changed = true;
    }

    if (changed) touched++;
  }

  console.log(`\nMerge results:`);
  console.log(`  images filled:     ${filledImage.toLocaleString()}`);
  console.log(`  range maps filled: ${filledRange.toLocaleString()}`);
  console.log(`  iucn status:       ${filledStatus.toLocaleString()}`);
  console.log(`  placeholders prom: ${placeholderPromoted.toLocaleString()}`);
  console.log(`  entries touched:  ${touched.toLocaleString()}`);
  console.log(`  cache grew to:    ${Object.keys(cache).length.toLocaleString()} entries`);

  if (dry) {
    console.log("\n--dry-run: not writing.");
    return;
  }
  saveCache(cache);
  console.log(`\nWrote ${CACHE_PATH}`);
}

main();