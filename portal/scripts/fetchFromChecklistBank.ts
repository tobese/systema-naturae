import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { recordTransformed, type TransformMeta } from "../../scripts/paths.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

// Kingdom awareness (mirrors buildData.ts / fetchSpeciesFromApi.ts): SN_KINGDOM
// selects which taxonomy file this import reads, so fungi/plantae imports
// never touch animalia.
interface KingdomConfig { label: string; input: string; rootDir: string; dataSuffix: string; colorRegistry: string; }
const SN_KINGDOM = process.env.SN_KINGDOM || "";
let _kcfg: KingdomConfig | undefined;
{
  const p = resolve(portalRoot, "data/kingdom-config.json");
  if (existsSync(p)) _kcfg = (JSON.parse(readFileSync(p, "utf-8")) as { kingdoms: Record<string, KingdomConfig> }).kingdoms[SN_KINGDOM];
}
const TAXONOMY_INPUT = _kcfg?.input ?? process.env.SN_INPUT ?? "data/taxonomy.json";
const TAXONOMY_PATH = resolve(portalRoot, TAXONOMY_INPUT);
const KINGDOM = SN_KINGDOM || "animalia";

// This importer only ever writes through importwrite — unlike
// fetchSpeciesFromApi.ts there is no direct-writeFileSync fallback. Its job
// stops at "fetch a row from ChecklistBank, shape it into our node fields,
// POST it"; whether that species already exists and which fields win on a
// conflict is importwrite's job, not this script's. See
// services/importwrite/README.md.
//
// SN_WORK_SLUG switches to a third mode: write the shaped species as
// scripts/importTransformed.py's record shape into that work-dir slug
// instead of POSTing at all, via scripts/paths.ts's recordTransformed()
// (the one shared-infrastructure module this file does import from --
// unlike sourceIds's SourceIds interface above, duplicated on purpose so
// peer importer scripts don't depend on each other, paths.ts exists
// specifically to be shared). Splits transformation from import: this
// process can run anywhere that can fetch ChecklistBank and reach the
// external volume, with no dependency on importwrite being up at all; see
// docs/data-sources.md's "split pipeline" paragraph.
const SN_WORK_SLUG = process.env.SN_WORK_SLUG || "";
const IMPORTWRITE_URL = process.env.IMPORTWRITE_URL || "";

// COL26.9 base release, the one currently held (see docs / checkColRelease.py).
// Override if/when a newer release is taken.
const CB_DATASET = process.env.COL_DATASET_KEY || "316321";
const CB_API = "https://api.checklistbank.org";

/**
 * Per-dataset record IDs for a species. Twin of the interface in
 * fetchSpeciesFromApi.ts (scripts in this repo are self-contained rather
 * than sharing types — see that file's comment) — keep both in sync if the
 * known-keys list changes.
 */
interface SourceIds {
  checklistbank?: string | string[];
  col?: string | string[];
  gbif?: string | string[];
  itis?: string | string[];
  wikidata?: string | string[];
  wfo?: string | string[];
  mycobank?: string | string[];
  worms?: string | string[];
  [source: string]: string | string[] | undefined;
}

interface CbName {
  scientificName: string;
  authorship?: string;
  rank: string;
  genus?: string;
  specificEpithet?: string;
}

interface CbUsage {
  id: string;
  name: CbName;
  status?: string;
  link?: string;
  extinct?: boolean;
}

interface CbVernacular {
  name: string;
  language?: string;
}

interface CbResult {
  id: string;
  usage: CbUsage;
  vernacularNames?: CbVernacular[];
}

interface CbSearchResponse {
  offset: number;
  limit: number;
  total: number;
  result: CbResult[];
}

interface FamilyNode {
  id: string;
  name: string;
  rank: string;
  commonName: string;
  appSlug: string;
  speciesCount: number;
  phylumName?: string;
  className?: string;
  orderName?: string;
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

function findFamily(slug: string): FamilyNode | null {
  const tax = JSON.parse(readFileSync(TAXONOMY_PATH, "utf-8"));
  let phy = "", cls = "", ord = "";
  function walk(n: Record<string, unknown>): FamilyNode | null {
    if (n.rank === "PHYLUM" && n.name) phy = (n.name as string).toLowerCase();
    if (n.rank === "CLASS" && n.name) cls = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) ord = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      return { ...n as unknown as FamilyNode, phylumName: phy, className: cls, orderName: ord };
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      const r = walk(c);
      if (r) return r;
    }
    return null;
  }
  return walk(tax);
}

function nameToId(name: string): string {
  return name.replace(/ /g, "_").toUpperCase();
}

function englishVernacular(names?: CbVernacular[]): string {
  if (!names) return "";
  return names.find(v => v.language === "eng")?.name ?? "";
}

// ChecklistBank's `usage.link` often points at the source dataset's own
// record — for COL entries originally compiled from ITIS, that's an
// itis.gov URL carrying the TSN. One ChecklistBank row can thus surface two
// of our known sourceIds keys (col + itis) at once.
const ITIS_LINK_RE = /itis\.gov\/.*search_value=(\d+)/i;
function extractItisTsn(link?: string): string | null {
  if (!link) return null;
  const m = link.match(ITIS_LINK_RE);
  return m ? m[1] : null;
}

async function findFamilyId(familyName: string): Promise<string> {
  const url = `${CB_API}/dataset/${CB_DATASET}/nameusage/search?q=${encodeURIComponent(familyName)}&rank=family&limit=5`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`ChecklistBank family search failed: ${res.status} ${await res.text()}`);
  const data = await res.json() as CbSearchResponse;
  const exact = data.result.find(r => r.usage.name.scientificName.toLowerCase() === familyName.toLowerCase());
  if (!exact) throw new Error(`ChecklistBank: no exact family match for "${familyName}" in dataset ${CB_DATASET}`);
  return exact.id;
}

async function fetchAcceptedSpecies(familyId: string, limit: number): Promise<CbResult[]> {
  const all: CbResult[] = [];
  let offset = 0;
  const pageSize = 100;
  let total = 0;
  while (true) {
    const url = `${CB_API}/dataset/${CB_DATASET}/nameusage/search?TAXON_ID=${familyId}&rank=species&status=accepted&limit=${pageSize}&offset=${offset}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`ChecklistBank species search failed: ${res.status} ${await res.text()}`);
    const data = await res.json() as CbSearchResponse;
    total = data.total;
    all.push(...data.result);
    offset += pageSize;
    if (offset >= total || offset >= limit) break;
    await sleep(200); // rate limit
  }
  return all;
}

interface ImportWriteSpeciesResult {
  name: string;
  id: string;
  uuid?: string;
  family?: string;
}

interface ImportWriteResult {
  added: ImportWriteSpeciesResult[];
  merged: ImportWriteSpeciesResult[];
  genusCreated: boolean;
}

function buildSpeciesNodes(rows: CbResult[], genusName: string): Record<string, unknown>[] {
  return rows.map(r => {
    const sciName = r.usage.name.scientificName;
    // col/itis are arrays everywhere else in the tree (a species can carry
    // more than one historical ID from the same source) — matching that
    // instead of sending a bare string avoids a same-ID-different-shape
    // diff on every re-import (importwrite's merge handles either shape
    // regardless, but there's no reason to introduce a new one here).
    const sourceIds: SourceIds = { col: [r.id] };
    const tsn = extractItisTsn(r.usage.link);
    if (tsn) sourceIds.itis = [tsn];

    const node: Record<string, unknown> = {
      id: nameToId(sciName),
      name: sciName,
      rank: "SPECIES",
      commonName: englishVernacular(r.vernacularNames),
      lineage: genusName,
      subspeciesCount: 0,
      // Don't fabricate — leave empty so enrichment can find real content,
      // same policy as fetchSpeciesFromApi.ts.
      description: "",
      sourcedFrom: "checklistbank",
      sourceIds,
    };
    if (r.usage.name.authorship) node.authorship = r.usage.name.authorship;
    if (r.usage.extinct) node.extinct = true;
    return node;
  });
}

async function postGenusToImportWrite(
  slug: string,
  family: FamilyNode,
  genusName: string,
  rows: CbResult[],
): Promise<ImportWriteResult> {
  const species = buildSpeciesNodes(rows, genusName);

  const res = await fetch(`${IMPORTWRITE_URL}/family/${slug}/species`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kingdom: KINGDOM,
      phylum: family.phylumName || "",
      class: family.className || "",
      order: family.orderName || "",
      genus: { id: `GENUS_${genusName.toUpperCase()}`, name: genusName },
      species,
    }),
  });
  if (!res.ok) throw new Error(`importwrite POST ${slug}/${genusName} failed: ${res.status} ${await res.text()}`);
  return res.json();
}

async function flushImportWrite(slug: string): Promise<void> {
  const res = await fetch(`${IMPORTWRITE_URL}/family/${slug}/flush`, { method: "POST" });
  if (!res.ok) throw new Error(`importwrite flush ${slug} failed: ${res.status} ${await res.text()}`);
}

async function main() {
  const slug = process.argv[2];
  const maxSpecies = process.argv[3] ? parseInt(process.argv[3], 10) : 999999;

  if (!slug) {
    console.log("Usage: npx tsx scripts/fetchFromChecklistBank.ts <appSlug> [maxSpecies]");
    console.log("  Fetches accepted species from ChecklistBank (Catalogue of Life).");
    console.log("  Requires IMPORTWRITE_URL (POSTs to importwrite directly) or");
    console.log("  SN_WORK_SLUG (writes transformed.jsonl for scripts/importTransformed.py");
    console.log("  to apply later, possibly on a different machine) — this importer");
    console.log("  never writes family files directly itself.");
    process.exit(1);
  }
  if (!SN_WORK_SLUG && !IMPORTWRITE_URL) {
    console.error("Either IMPORTWRITE_URL or SN_WORK_SLUG is required.");
    process.exit(1);
  }

  const family = findFamily(slug);
  if (!family) {
    console.error(`Family "${slug}" not found in taxonomy.json`);
    process.exit(1);
  }

  console.log(`${family.name} (${family.className}/${family.orderName}/${family.appSlug}) via ChecklistBank dataset ${CB_DATASET}`);

  const familyId = await findFamilyId(family.name);
  console.log(`  ChecklistBank family id: ${familyId}`);

  const results = await fetchAcceptedSpecies(familyId, maxSpecies);
  console.log(`  Found ${results.length} accepted species`);
  if (results.length === 0) {
    console.log("  Nothing to send — exit");
    process.exit(0);
  }

  const genusMap = new Map<string, CbResult[]>();
  for (const r of results) {
    const genus = r.usage.name.genus || r.usage.name.scientificName.split(" ")[0] || "Unknown";
    if (!genusMap.has(genus)) genusMap.set(genus, []);
    genusMap.get(genus)!.push(r);
  }

  if (SN_WORK_SLUG) {
    // Split-pipeline mode: write scripts/importTransformed.py's record
    // shape instead of POSTing. Each record carries its own placement
    // (kingdom/phylum/class/order/family/genus) because that script's
    // grouping doesn't assume one file is one family -- this one always
    // is, but the shape is the same either way.
    const records = Array.from(genusMap.entries()).flatMap(([genusName, rows]) =>
      buildSpeciesNodes(rows, genusName).map((species) => ({
        kingdom: KINGDOM,
        phylum: family.phylumName || "",
        class: family.className || "",
        order: family.orderName || "",
        family: slug,
        genus: genusName,
        species,
      })),
    );
    const meta: TransformMeta = {
      source: "checklistbank",
      sourceDatasetId: CB_DATASET,
      sourceUrl: `${CB_API}/dataset/${CB_DATASET}`,
      fetchedAt: new Date().toISOString(),
      transformer: "fetchFromChecklistBank.ts",
    };
    const path = recordTransformed(SN_WORK_SLUG, "transformed.jsonl", records, meta);
    console.log(`  wrote ${records.length} records to ${path}`);
    console.log(`  apply later with: IMPORTWRITE_URL=... python3 scripts/importTransformed.py ${SN_WORK_SLUG}`);
    return;
  }

  let added = 0, merged = 0, newUuids = 0, crossFamily = 0;
  for (const [genusName, rows] of genusMap) {
    const result = await postGenusToImportWrite(slug, family, genusName, rows);
    added += result.added.length;
    merged += result.merged.length;
    newUuids += result.added.filter((s) => s.uuid).length;
    // `family` is set only when importwrite's cross-family identity check
    // (services/importwrite/crossfamily.go) found this species already
    // living in a DIFFERENT family and merged it there instead of adding
    // a duplicate here -- the fix for the 2026-10-18 incident. Surfaced so
    // a run against real data shows it happening, not just the add/merge
    // counts.
    for (const m of result.merged) {
      if (m.family && m.family !== slug) crossFamily++;
    }
  }
  await flushImportWrite(slug);

  console.log(`  importwrite: ${added} added, ${merged} merged`);
  if (newUuids > 0) console.log(`  🆔 ${newUuids} new species assigned a uuid by importwrite`);
  if (crossFamily > 0) console.log(`  🔀 ${crossFamily} already existed in a different family -- merged there instead of duplicated`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
