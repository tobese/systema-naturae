import { readFileSync, writeFileSync } from "fs";
import { execSync } from "child_process";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

const WIKI_URL = "https://en.wikipedia.org/api/rest_v1/page/summary";
const RATE_LIMIT_MS = 150;

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

interface WikiSummary {
  title?: string;
  extract?: string;
  description?: string;
}

async function fetchWiki(sciName: string): Promise<WikiSummary | null> {
  try {
    const url = `${WIKI_URL}/${encodeURIComponent(sciName.replace(/_/g, " "))}`;
    const res = await fetch(url, { headers: { "User-Agent": "SystemaNaturae/1.0" } });
    if (!res.ok) return null;
    return await res.json() as WikiSummary;
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

async function enrichNode(node: any, enriched: { ok: number; fail: number; skip: number }) {
  if (!node) return;
  if (node.rank !== "SPECIES") {
    for (const c of (node.children ?? [])) await enrichNode(c, enriched);
    return;
  }

  if (node.sourcedFrom === "wikipedia" && (node.description?.length ?? 0) > 40) {
    enriched.skip++;
    return;
  }

  await sleep(RATE_LIMIT_MS);
  const wiki = await fetchWiki(node.name as string);

  if (wiki && wiki.extract) {
    const extract = wiki.extract.replace(/<[^>]+>/g, "").trim();
    const firstSentence = extract.split(/(?<=[.!?])\s+/)[0] + ".";
    node.description = firstSentence;
    node.sourcedFrom = "wikipedia";
    if (wiki.description && wiki.description.length < 80) node.commonName = wiki.description;
    enriched.ok++;
  } else {
    enriched.fail++;
  }
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
    console.error("Provide one or more family appSlugs to enrich from Wikipedia.");
    process.exit(1);
  }

  const files = findDataFiles(slugs);
  if (files.size === 0) {
    console.error("No data files found for the provided slugs.");
    process.exit(1);
  }

  for (const slug of slugs) {
    if (!files.has(slug)) console.warn(`  ⚠ No data file found for ${slug}`);
  }

  console.log(`Enriching ${files.size} families from Wikipedia…\n`);

  let totalOk = 0;
  let totalFail = 0;
  let totalSkip = 0;

  for (const [slug, path] of files) {
    const data = JSON.parse(readFileSync(path, "utf-8"));
    const total = countSpecies(data);
    const enriched = { ok: 0, fail: 0, skip: 0 };

    // Pre-count candidates
    function countCandidates(node: any) {
      if (!node) return;
      if (node.rank !== "SPECIES") { for (const c of (node.children ?? [])) countCandidates(c); return; }
      if (node.sourcedFrom !== "wikipedia" || (node.description?.length ?? 0) <= 40) enriched.fail++;
      else enriched.skip++;
    }
    countCandidates(data);

    const candidates = enriched.fail;
    enriched.ok = 0;
    enriched.fail = 0;

    // Enrich
    await enrichNode(data, enriched);

    writeFileSync(path, JSON.stringify(data, null, 2) + "\n");

    totalOk += enriched.ok;
    totalFail += enriched.fail;
    totalSkip += enriched.skip;

    const pct = candidates > 0 ? Math.round((enriched.ok / candidates) * 100) : 100;
    console.log(`  ${slug}: ${enriched.ok} enriched, ${enriched.fail} failed, ${enriched.skip} skipped (${candidates} candidates, ${pct}%) — ${total} spp`);
  }

  console.log(`\nDone. ${totalOk} enriched, ${totalFail} failed, ${totalSkip} skipped across ${files.size} families.`);
}

main();
