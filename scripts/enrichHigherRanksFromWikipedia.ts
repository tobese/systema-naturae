// Fills missing CLASS/ORDER `description` fields in the two taxonomy source
// files (portal/data/taxonomy.json for Animalia, portal/data/taxonomy-plantae-
// snippet.json for Plantae) from the live Wikipedia API. Unlike species-level
// enrichment (scripts/enrichFromWikipedia.ts), this never checks the offline
// SQLite dump - that DB only ever imported pages matching a species-name
// candidate list (see scripts/buildWikipediaDb.py's `wanted` set), so
// Class/Order-level topic pages like "Coleoptera" or "Insecta" simply aren't
// in it (confirmed directly). At only a few hundred remaining lookups, the
// live API alone is fast enough.
//
// Real, portal-wide data - benefits every consumer of taxonomy.json, not
// just book-view. Idempotent (skips anything already populated) and never
// fabricates: a miss or disambiguation is left empty, same rule every
// enrichment script in this repo follows.
//
// Usage: npx tsx scripts/enrichHigherRanksFromWikipedia.ts [--dry-run]
import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..");

const TAXONOMY_FILES = [
  join(REPO_ROOT, "portal/data/taxonomy.json"),
  join(REPO_ROOT, "portal/data/taxonomy-plantae-snippet.json"),
];

const WIKI_API = "https://en.wikipedia.org/w/api.php";
const BATCH_SIZE = 50;
const DELAY_MS = 1500;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  description?: string;
  children?: TaxonNode[];
}

interface FetchResult {
  extract: string;
}

// Same MediaWiki batch-fetch mechanics as scripts/enrichFromWikipedia.ts's
// fetchBatch() (live-API branch only) - proven redirect/normalization
// handling, deliberately not re-abstracted into a shared module since both
// scripts are meant to stay simple, standalone, one-off tools.
async function fetchBatch(titles: string[]): Promise<Map<string, FetchResult>> {
  const params = new URLSearchParams({
    action: "query",
    titles: titles.join("|"),
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
    for (const r of data.query?.redirects ?? []) redirects.set(r.from, r.to);
    for (const r of data.query?.normalized ?? []) {
      if (!redirects.has(r.from)) redirects.set(r.from, r.to);
    }

    const lookup = new Map<string, number>();
    for (const [id, page] of Object.entries(pages)) {
      const p = page as any;
      if (p.missing !== undefined) continue;
      lookup.set(p.title, Number(id));
    }

    const result = new Map<string, FetchResult>();
    for (const title of titles) {
      const resolved = redirects.get(title) ?? title;
      const id = lookup.get(resolved);
      if (id == null) continue;
      const p = pages[id] as any;
      if (!p.extract) continue;
      let extract = (p.extract as string).replace(/<[^>]+>/g, "").trim();
      // Wikipedia's plaintext extracts often leave a stray leading
      // semicolon or empty parens where an IPA-pronunciation template got
      // stripped (e.g. "Bivalvia () or..." / "Gastropods (;  previously
      // known..."). Clean it up rather than shipping the artifact.
      extract = extract.replace(/\(\s*;\s*/g, "(").replace(/\(\s*\)\s?/g, "").replace(/ {2,}/g, " ");
      // First 2 sentences - a bit more substantial than the single-sentence
      // species blurb, since this renders as a real "Part intro" paragraph.
      const sentences = extract.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ");
      if (sentences.length > 20) result.set(title, { extract: sentences });
    }
    return result;
  } catch {
    return new Map();
  }
}

interface Candidate {
  node: TaxonNode;
  rank: string;
}

function collectCandidates(root: TaxonNode, out: Candidate[]): void {
  if ((root.rank === "CLASS" || root.rank === "ORDER") && !root.description) {
    out.push({ node: root, rank: root.rank });
  }
  for (const child of root.children ?? []) collectCandidates(child, out);
}

async function enrichBatchByName(
  candidates: Candidate[],
  titleFor: (c: Candidate) => string | undefined,
): Promise<Candidate[]> {
  const stillMissing: Candidate[] = [];
  for (let i = 0; i < candidates.length; i += BATCH_SIZE) {
    const batch = candidates.slice(i, i + BATCH_SIZE);
    const titled = batch
      .map((c) => ({ c, title: titleFor(c) }))
      .filter((x): x is { c: Candidate; title: string } => Boolean(x.title));
    if (titled.length === 0) {
      stillMissing.push(...batch);
      continue;
    }
    await sleep(DELAY_MS);
    const result = await fetchBatch(titled.map((x) => x.title));
    const hit = new Set<Candidate>();
    for (const { c, title } of titled) {
      const r = result.get(title);
      if (r) {
        c.node.description = r.extract;
        hit.add(c);
      }
    }
    for (const c of batch) if (!hit.has(c)) stillMissing.push(c);
  }
  return stillMissing;
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");

  for (const path of TAXONOMY_FILES) {
    const data: TaxonNode = JSON.parse(readFileSync(path, "utf-8"));
    const candidates: Candidate[] = [];
    collectCandidates(data, candidates);

    const classCount = candidates.filter((c) => c.rank === "CLASS").length;
    const orderCount = candidates.filter((c) => c.rank === "ORDER").length;
    console.log(`\n${path}`);
    console.log(`  ${classCount} classes, ${orderCount} orders missing description`);

    if (candidates.length === 0) continue;
    if (dryRun) {
      console.log(`  (dry run - not fetching)`);
      continue;
    }

    // Pass 1: scientific name. Pass 2: commonName, only for whatever pass 1
    // still missed (many CLASS/ORDER nodes have no Wikipedia article under
    // their exact scientific name but do under the common-name equivalent,
    // e.g. Coleoptera -> Beetles).
    const afterNamePass = await enrichBatchByName(candidates, (c) => c.node.name);
    const afterCommonNamePass = await enrichBatchByName(afterNamePass, (c) => c.node.commonName);

    const filled = candidates.length - afterCommonNamePass.length;
    console.log(`  ${filled}/${candidates.length} filled from Wikipedia`);
    if (afterCommonNamePass.length > 0) {
      console.log(
        `  still missing: ${afterCommonNamePass.map((c) => c.node.name).slice(0, 15).join(", ")}${
          afterCommonNamePass.length > 15 ? ", ..." : ""
        }`,
      );
    }

    writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
  }
}

main();
