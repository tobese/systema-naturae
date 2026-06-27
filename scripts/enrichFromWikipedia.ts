import { readFileSync, writeFileSync } from "fs";
import { execSync } from "child_process";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";
import { existsSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

const SQLITE_DB = "/Volumes/WikiDump/wiki-pages.sqlite";
const WIKI_API = "https://en.wikipedia.org/w/api.php";
const BATCH_SIZE = 50;
const DELAY_MS = 1500;
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+$/;

interface BatchResult {
  extract: string;
  description?: string;
}

function lookupLocalBatch(titles: string[]): Map<string, BatchResult> {
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
    const res = spawnSync("python3", ["-c", script, SQLITE_DB, JSON.stringify(titles)], { encoding: "utf-8" });
    if (res.status !== 0 || !res.stdout.trim()) return new Map();
    const rows = JSON.parse(res.stdout.trim()) as Record<string, BatchResult>;
    return new Map(Object.entries(rows));
  } catch {
    return new Map();
  }
}

async function fetchBatch(titles: string[]): Promise<Map<string, BatchResult>> {
  const local = lookupLocalBatch(titles);
  const remote = titles.filter(t => !local.has(t));

  if (remote.length === 0) return local;

  const params = new URLSearchParams({
    action: "query",
    titles: remote.join("|"),
    prop: "extracts",
    exintro: "1",
    explaintext: "1",
    exlimit: String(BATCH_SIZE),
    redirects: "1",
    format: "json",
    origin: "*",
  });

  try {
    const res = await fetch(`${WIKI_API}?${params}`, {
      headers: { "User-Agent": "SystemaNaturae/1.0" },
    });
    if (!res.ok) return new Map();
    const data: any = await res.json();
    const pages = data.query?.pages ?? {};
    const redirects = new Map<string, string>();
    for (const r of data.query?.redirects ?? []) {
      redirects.set(r.from, r.to);
    }
    for (const r of data.query?.normalized ?? []) {
      if (!redirects.has(r.from)) redirects.set(r.from, r.to);
    }

    const lookup = new Map<string, number>();
    for (const [id, page] of Object.entries(pages)) {
      const p = page as any;
      if (p.missing) continue;
      lookup.set(p.title, Number(id));
    }

    const result = new Map<string, BatchResult>();
    for (const title of remote) {
      const resolved = redirects.get(title) ?? title;
      const id = lookup.get(resolved);
      if (id == null) continue;
      const p = pages[id] as any;
      if (!p.extract) continue;
      const extract = p.extract.replace(/<[^>]+>/g, "").trim();
      const firstSentence = extract.split(/(?<=[.!?])\s+/)[0] + ".";
      result.set(title, {
        extract: firstSentence,
        description: p.description?.length < 80 ? p.description : undefined,
      });
    }
    for (const [k, v] of local) result.set(k, v);
    return result;
  } catch {
    return local;
  }
}

function countSpecies(node: any): number {
  let n = 0;
  if (node.rank === "SPECIES") n++;
  for (const c of node.children ?? []) n += countSpecies(c);
  return n;
}

function collectSpecies(node: any, out: any[]) {
  if (!node) return;
  if (node.rank !== "SPECIES") {
    for (const c of node.children ?? []) collectSpecies(c, out);
    return;
  }
  if (node.sourcedFrom === "wikipedia" && (node.description?.length ?? 0) > 40) return;
  if (!BINOMIAL_RE.test(node.name as string)) return;
  out.push(node);
}

function getAllDataFiles(): Map<string, string> {
  const out = execSync(
    `find ${root} -path "*/src/data/*.json" -not -path "*/node_modules/*" -type f`,
    { encoding: "utf-8" }
  ).trim();
  const files = new Map<string, string>();
  for (const f of out.split("\n").filter(Boolean)) {
    const match = f.match(/\/([^/]+)\/src\/data\/\1\.json$/);
    if (match) files.set(match[1], f);
  }
  return files;
}

async function main() {
  const args = process.argv.slice(2);
  const slugs = args.filter(a => !a.startsWith("--"));
  const live = args.includes("--live");

  let files: Map<string, string>;
  if (slugs.length > 0) {
    files = new Map();
    for (const slug of slugs) {
      const result = execSync(
        `find ${root} -path "*/${slug}/src/data/${slug}.json" -not -path "*/node_modules/*" -type f`,
        { encoding: "utf-8" }
      ).trim();
      if (result) files.set(slug, result.split("\n")[0]);
    }
  } else {
    files = getAllDataFiles();
  }

  if (files.size === 0) {
    console.error("No data files found.");
    process.exit(1);
  }

  console.log(`Enriching ${files.size} families from Wikipedia (batches of ${BATCH_SIZE})...\n`);

  let totalOk = 0;
  let totalFail = 0;
  let totalSkip = 0;
  let totalApiCalls = 0;
  let familyCount = 0;

  for (const [slug, path] of files) {
    familyCount++;
    const data = JSON.parse(readFileSync(path, "utf-8"));
    const total = countSpecies(data);

    const candidates: any[] = [];
    collectSpecies(data, candidates);
    let alreadyEnriched = 0;
    (function walk(n: any) {
      if (n.rank === "SPECIES" && n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40) alreadyEnriched++;
      for (const c of n.children ?? []) walk(c);
    })(data);

    if (candidates.length === 0) {
      console.log(`  ${slug}: 0 candidates, ${alreadyEnriched} already enriched — ${total} spp`);
      totalSkip += alreadyEnriched;
      continue;
    }

    let ok = 0;
    let fail = 0;

    for (let i = 0; i < candidates.length; i += BATCH_SIZE) {
      const batch = candidates.slice(i, i + BATCH_SIZE);
      const names = batch.map(n => n.name as string);
      let result: Map<string, BatchResult>;
      if (live) {
        await sleep(DELAY_MS);
        totalApiCalls++;
        result = await fetchBatch(names);
      } else {
        result = lookupLocalBatch(names);
      }

      for (const node of batch) {
        const r = result.get(node.name as string);
        if (r) {
          node.description = r.extract;
          node.sourcedFrom = "wikipedia";
          if (r.description) node.commonName = r.description;
          ok++;
        } else {
          fail++;
        }
      }

      const pct = i + batch.length;
      if (pct % 200 === 0 || pct === candidates.length) {
        process.stdout.write(` ${slug}: ${ok}/${pct}\n`);
      }
    }

    writeFileSync(path, JSON.stringify(data, null, 2) + "\n");

    totalOk += ok;
    totalFail += fail;
    totalSkip += alreadyEnriched;
    const pct = candidates.length > 0 ? Math.round((ok / candidates.length) * 100) : 100;
    console.log(`  ${slug}: ${ok} enriched, ${fail} failed, ${alreadyEnriched} skipped (${candidates.length} candidates, ${pct}%) — ${total} spp\n`);
  }

  console.log(`\nDone. ${totalOk} enriched, ${totalFail} failed, ${totalSkip} skipped across ${files.size} families (${totalApiCalls} API calls).`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
