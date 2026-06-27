import { readFileSync, writeFileSync } from "fs";
import { execSync } from "child_process";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

const WIKI_URL = "https://en.wikipedia.org/api/rest_v1/page/summary";

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

interface WikiSummary {
  title?: string;
  extract?: string;
  description?: string;
}

const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+$/;

async function fetchWithRetry(sciName: string): Promise<WikiSummary | null> {
  const url = `${WIKI_URL}/${encodeURIComponent(sciName.replace(/_/g, " "))}`;
  try {
    const res = await fetch(url, { headers: { "User-Agent": "SystemaNaturae/1.0" } });
    if (res.ok) return await res.json() as WikiSummary;
    return null;
  } catch {
    return null;
  }
}

function countSpecies(node: any): number {
  let n = 0;
  if (node.rank === "SPECIES") n++;
  for (const c of (node.children ?? [])) n += countSpecies(c);
  return n;
}

function collectSpecies(node: any, out: any[]) {
  if (!node) return;
  if (node.rank !== "SPECIES") {
    for (const c of (node.children ?? [])) collectSpecies(c, out);
    return;
  }
  if (node.sourcedFrom === "wikipedia" && (node.description?.length ?? 0) > 40) return;
  if (!BINOMIAL_RE.test(node.name as string)) return;
  out.push(node);
}

function findDataFiles(slugs: string[]): Map<string, string> {
  const found = new Map<string, string>();
  for (const slug of slugs) {
    try {
      const result = execSync(
        `find ${root} -path "*/${slug}/src/data/${slug}.json" -not -path "*/node_modules/*" -type f`,
        { encoding: "utf-8" }
      ).trim();
      if (result) found.set(slug, result.split("\n")[0]);
    } catch { /* not found */ }
  }
  return found;
}

async function main() {
  const args = process.argv.slice(2);
  const slugs = args.filter(a => !a.startsWith("--"));

  if (slugs.length === 0) {
    console.error("Usage: npx tsx enrichFromWikipedia.ts <family-slug> [family-slug...]");
    process.exit(1);
  }

  const files = findDataFiles(slugs);
  if (files.size === 0) {
    console.error("No data files found for the provided slugs.");
    process.exit(1);
  }

  for (const slug of slugs) {
    if (!files.has(slug)) console.warn(`  WARNING No data file found for ${slug}`);
  }

  console.log(`Enriching ${files.size} families from Wikipedia...\n`);

  let totalOk = 0;
  let totalFail = 0;
  let totalSkip = 0;

  for (const [slug, path] of files) {
    const data = JSON.parse(readFileSync(path, "utf-8"));
    const total = countSpecies(data);

    const candidates: any[] = [];
    collectSpecies(data, candidates);
    let alreadyEnriched = 0;
    (function walk(node: any) {
      if (node.rank === "SPECIES" && node.sourcedFrom === "wikipedia" && (node.description?.length ?? 0) > 40) alreadyEnriched++;
      for (const c of (node.children ?? [])) walk(c);
    })(data);
    const skip = alreadyEnriched;

    let ok = 0;
    let fail = 0;

    for (let i = 0; i < candidates.length; i++) {
      const node = candidates[i];
      await sleep(2500);

      const wiki = await fetchWithRetry(node.name as string);

      if (wiki && wiki.extract) {
        const extract = wiki.extract.replace(/<[^>]+>/g, "").trim();
        const firstSentence = extract.split(/(?<=[.!?])\s+/)[0] + ".";
        node.description = firstSentence;
        node.sourcedFrom = "wikipedia";
        if (wiki.description && wiki.description.length < 80) node.commonName = wiki.description;
        ok++;
        process.stdout.write(".");
      } else {
        fail++;
        process.stdout.write("x");
      }

      if ((i + 1) % 50 === 0) process.stdout.write(` ${i + 1}/${candidates.length}\n`);
      if ((i + 1) % 20 === 0) await sleep(5000);
    }

    writeFileSync(path, JSON.stringify(data, null, 2) + "\n");

    totalOk += ok;
    totalFail += fail;
    totalSkip += skip;

    const pct = candidates.length > 0 ? Math.round((ok / candidates.length) * 100) : 100;
    process.stdout.write(`\n`);
    console.log(`  ${slug}: ${ok} enriched, ${fail} failed, ${skip} skipped (${candidates.length} candidates, ${pct}%) — ${total} spp`);
  }

  console.log(`\nDone. ${totalOk} enriched, ${totalFail} failed, ${totalSkip} skipped across ${files.size} families.`);
}

main();
