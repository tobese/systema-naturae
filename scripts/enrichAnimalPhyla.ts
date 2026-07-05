/**
 * Quick Wikipedia enrichment for the 8 new animal phyla.
 * Usage: npx tsx scripts/enrichAnimalPhyla.ts [--live]
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const SQLITE_DB = "/Volumes/WikiDump/wiki-pages.sqlite";
const WIKI_API = "https://en.wikipedia.org/w/api.php";
const BATCH_SIZE = 50;
const DELAY_MS = 1500;
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+$/;

const PHYLA = [
  "phoronida", "loricifera", "priapulida", "entoprocta",
  "gnathostomulida", "onychophora", "gastrotricha", "xenacoelomorpha",
];

function collectFamilyFiles(): string[] {
  const files: string[] = [];
  for (const phylum of PHYLA) {
    const phylumDir = resolve(root, phylum);
    if (!existsSync(phylumDir)) continue;
    const result = spawnSync("find", [phylumDir, "-name", "*.json", "-path", "*/src/data/*", "-type", "f"], {
      encoding: "utf-8", timeout: 5000,
    });
    if (result.status === 0 && result.stdout.trim()) {
      for (const f of result.stdout.trim().split("\n").filter(Boolean)) {
        files.push(f);
      }
    }
  }
  return files;
}

function lookupLocalBatch(titles: string[]): Map<string, { extract: string; description?: string }> {
  if (!existsSync(SQLITE_DB) || titles.length === 0) return new Map();
  const script = `
import json, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
titles = json.loads(sys.argv[2])
rows = {}
for row in db.execute(f"SELECT title, description, extract FROM pages WHERE title IN ({','.join('?' for _ in titles)})", titles):
    rows[row[0]] = {'description': row[1], 'extract': row[2]}
print(json.dumps(rows))
`;
  try {
    const res = spawnSync("python3", ["-c", script, SQLITE_DB, JSON.stringify(titles)], { encoding: "utf-8", timeout: 10000 });
    if (res.status !== 0 || !res.stdout.trim()) return new Map();
    return new Map(Object.entries(JSON.parse(res.stdout.trim())));
  } catch { return new Map(); }
}

async function fetchBatch(titles: string[]): Promise<Map<string, { extract: string; description?: string }>> {
  const local = lookupLocalBatch(titles);
  const remote = titles.filter(t => !local.has(t));
  if (remote.length === 0) return local;

  const params = new URLSearchParams({
    action: "query", titles: remote.join("|"),
    prop: "extracts", exintro: "1", explaintext: "1",
    exlimit: String(BATCH_SIZE), redirects: "1", format: "json", origin: "*",
  });
  try {
    const res = await fetch(`${WIKI_API}?${params}`, {
      headers: { "User-Agent": "SystemaNaturae/1.0" },
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return local;
    const data: any = await res.json();
    const pages = data.query?.pages ?? {};
    const redirects = new Map<string, string>();
    for (const r of data.query?.redirects ?? []) redirects.set(r.from, r.to);
    for (const r of data.query?.normalized ?? []) if (!redirects.has(r.from)) redirects.set(r.from, r.to);

    const lookup = new Map<string, number>();
    for (const [id, page] of Object.entries(pages)) {
      const p = page as any;
      if (p.missing) continue;
      lookup.set(p.title, Number(id));
    }
    for (const title of remote) {
      const resolved = redirects.get(title) ?? title;
      const id = lookup.get(resolved);
      if (id == null) continue;
      const p = pages[id] as any;
      if (!p.extract) continue;
      const extract = p.extract.replace(/<[^>]+>/g, "").trim();
      const firstSentence = extract.split(/(?<=[.!?])\s+/)[0] + ".";
      local.set(title, {
        extract: firstSentence,
        description: p.description?.length < 80 ? p.description : undefined,
      });
    }
    return local;
  } catch { return local; }
}

function countSpecies(node: any): number {
  let n = 0;
  if (node.rank === "SPECIES") n++;
  for (const c of node.children ?? []) n += countSpecies(c);
  return n;
}

async function main() {
  const live = process.argv.includes("--live");
  const files = collectFamilyFiles();
  console.log(`Found ${files.length} family files across ${PHYLA.length} phyla\n`);

  let totalOk = 0, totalFail = 0, totalSkip = 0, totalApi = 0;

  for (const filePath of files) {
    const data = JSON.parse(readFileSync(filePath, "utf-8"));
    const total = countSpecies(data);

    // Collect candidate species (not already enriched)
    const candidates: any[] = [];
    (function walk(n: any) {
      if (n.rank === "SPECIES") {
        if (n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40) return;
        if (!BINOMIAL_RE.test(n.name as string)) return;
        candidates.push(n);
      }
      for (const c of n.children ?? []) walk(c);
    })(data);

    let already = 0;
    (function walk(n: any) {
      if (n.rank === "SPECIES" && n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40) already++;
      for (const c of n.children ?? []) walk(c);
    })(data);

    if (candidates.length === 0) {
      console.log(`  ${data.name}: 0 candidates, ${already} enriched — ${total} spp`);
      totalSkip += already;
      continue;
    }

    let ok = 0, fail = 0;
    for (let i = 0; i < candidates.length; i += BATCH_SIZE) {
      const batch = candidates.slice(i, i + BATCH_SIZE);
      const names = batch.map(n => n.name);
      let result: Map<string, { extract: string; description?: string }>;

      if (live) {
        await sleep(DELAY_MS);
        totalApi++;
        result = await fetchBatch(names);
      } else {
        result = lookupLocalBatch(names);
      }

      for (const node of batch) {
        const r = result.get(node.name);
        if (r && r.extract && r.extract.length > 20) {
          node.description = r.extract;
          node.sourcedFrom = "wikipedia";
          if (r.description) node.commonName = r.description;
          ok++;
        } else {
          fail++;
        }
      }
    }

    writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
    totalOk += ok; totalFail += fail; totalSkip += already;
    const pct = candidates.length > 0 ? Math.round((ok / candidates.length) * 100) : 100;
    console.log(`  ${data.name}: ${ok} enriched, ${fail} failed, ${already} skipped (${candidates.length} cand, ${pct}%) — ${total} spp`);
  }

  console.log(`\nDone. ${totalOk} enriched, ${totalFail} failed, ${totalSkip} skipped (${totalApi} API calls)`);
}

main().catch(console.error);
