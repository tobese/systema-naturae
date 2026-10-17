/**
 * Recount where the tree's content came from, and write the table the Sources
 * modal renders.
 *
 * Two different questions, two different fields, and conflating them is the
 * mistake this script exists to avoid:
 *
 *   - `sourcedFrom` (4.0M nodes) — the provenance of the *text and names*. What
 *     docs/data-sources.md tabulates.
 *   - `sourceIds` (3.35M nodes) — the provenance of the *record*: which dataset
 *     supplied the name, keyed by dataset (`col`, `wfo`, `checklistbank`,
 *     `mycobank`, …). A node usually carries both.
 *
 * So the report carries both tallies, per kingdom and in total, because the
 * modal can be opened in any of the eight.
 *
 * Licences are not written here. They come from the manifest on the external
 * volume (`SN_SOURCES_ROOT/manifest.json`, 149 datasets, one row per source with
 * its licence and citation identifier), which is the same machine-readable form
 * docs/data-sources.md describes. When the volume is unmounted the report still
 * generates, with `licence: null` and `unresolved: true` — an honest blank
 * rather than an invented "various".
 *
 *   npx tsx scripts/aggregateSources.ts
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "fs";
import { resolve, join, dirname, basename, sep } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");
const taxDir = resolve(portalRoot, "..", "taxonomy");
const outPath = resolve(portalRoot, "public", "data", "sources-report.json");

const SOURCES_ROOT = process.env.SN_SOURCES_ROOT ?? "/Volumes/MacieExternal/sources";
const manifestPath = resolve(SOURCES_ROOT, "manifest.json");

type Manifest = Record<string, { title?: string; url?: string; identifier?: string; licence?: string; status?: string }>;

/**
 * Ids stamped on nodes that are not manifest keys: a container name covering
 * several datasets, or a source that was never downloaded.
 */
const ALIASES: Record<string, { datasets: string[]; note?: string }> = {
  // Container names. A node from ITIS and one from the Global Lepidoptera Index
  // are both `checklistbank` in the tree; only the manifest tells them apart.
  checklistbank: { datasets: ["checklistbank-2144", "checklistbank-55434"], note: "container name — one id for every ChecklistBank dataset; see Datasets" },
  "catalogue of life": { datasets: ["catalogue-of-life"] },
  col: { datasets: ["catalogue-of-life"] },
  wfo: { datasets: ["wfo-plant-list"] },
  gbif: { datasets: ["gbif-backbone"] },
  commons: { datasets: ["wikimedia-commons"] },
  nmnh: { datasets: ["nmnh"] },
  // ITIS arrived through ChecklistBank 2144 (CC0), not the standalone manifest
  // row, which records no licence at all.
  itis: { datasets: ["checklistbank-2144"] },
  // Never downloaded, or not a dataset at all.
  wikipedia: { datasets: [], note: "article text, fetched per species; no archive" },
  wikidata: { datasets: [], note: "statements via the API; images live in wiki-images.json" },
  powo: { datasets: [], note: "fetched per species; no archive" },
  nzpcn: { datasets: [], note: "1 node, permission-based" },
  websearch: { datasets: [], note: "mixed provenance, some not openly licensed" },
  ollama: { datasets: [], note: "generated locally by a model; not an external source" },
  generated: { datasets: [], note: "template-generated from lineage" },
  none: { datasets: [], note: "no provenance recorded — a blind spot, not a source" },
  // The Species File Group, one manifest row each.
  "afrotropical bees": { datasets: ["afrotropical-bees"] },
  "aphid species file": { datasets: ["aphid-species-file"] },
  "chrysididae species file": { datasets: ["species-file-chrysididae"] },
  "cockroach species file": { datasets: ["species-file-cockroach"] },
  "coleorrhyncha species file": { datasets: ["species-file-coleorrhyncha"] },
  "coreoidea species file": { datasets: ["species-file-coreoidea"] },
  "dermaptera species file": { datasets: ["species-file-dermaptera"] },
  "embioptera species file": { datasets: ["species-file-embioptera"] },
  "grylloblattodea species file": { datasets: ["species-file-grylloblattodea"] },
  "lygaeoidea species file": { datasets: ["species-file-lygaeoidea"] },
  "mantodea species file": { datasets: ["species-file-mantodea"] },
  "mantophasmatodea species file": { datasets: ["species-file-mantophasmatodea"] },
  "orthoptera species file": { datasets: ["orthoptera"] },
  "phasmida species file": { datasets: ["species-file-phasmida"] },
  "plecoptera species file": { datasets: ["species-file-plecoptera"] },
  "psocodea species file": { datasets: ["species-file-psocodea"] },
  "zoraptera species file": { datasets: ["species-file-zoraptera"] },
};

function loadManifest(): Manifest | null {
  if (!existsSync(manifestPath)) {
    console.warn(`WARN  ${manifestPath} not found — licences will be omitted.`);
    console.warn(`      The external volume looks unmounted; the counts are unaffected.`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(manifestPath, "utf8")).sources ?? null;
  } catch (e) {
    console.warn(`WARN  ${manifestPath} unreadable (${(e as Error).message}) — licences will be omitted.`);
    return null;
  }
}

interface Tally { nodes: number; families: number; sourcedFrom: Record<string, number>; sourceIds: Record<string, number>; }

function newTally(): Tally {
  return { nodes: 0, families: 0, sourcedFrom: {}, sourceIds: {} };
}

/**
 * Family data files only — `…/<family>/src/data/<family>.json`. The filename has
 * to match the family directory, because `src/data/` also holds sidecars
 * (`felidae/src/data/continents.json`) that are not trees and must not be
 * counted as families or tallied as nodes.
 */
function walkFamilies(dir: string, out: string[] = []): string[] {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) {
      walkFamilies(p, out);
      continue;
    }
    if (!e.endsWith(".json") || !p.includes(`${sep}src${sep}data${sep}`)) continue;
    const family = basename(dirname(dirname(dirname(p))));
    if (e === `${family}.json`) out.push(p);
  }
  return out;
}

/** The only node fields this tally reads. */
interface TreeNode {
  sourcedFrom?: unknown;
  sourceIds?: Record<string, unknown> | null;
  children?: TreeNode[];
  speciesList?: TreeNode[];
}

function tallyTree(root: TreeNode, t: Tally) {
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    if (!n || typeof n !== "object") continue;
    t.nodes++;
    const sf = n.sourcedFrom;
    if (typeof sf === "string" && sf) t.sourcedFrom[sf] = (t.sourcedFrom[sf] ?? 0) + 1;
    const si = n.sourceIds;
    if (si && typeof si === "object") {
      for (const k of Object.keys(si)) t.sourceIds[k] = (t.sourceIds[k] ?? 0) + 1;
    }
    const kids = n.children;
    if (Array.isArray(kids)) for (const c of kids) stack.push(c);
    const list = n.speciesList;
    if (Array.isArray(list)) for (const s of list) stack.push(s);
  }
}

const manifest = loadManifest();
const kingdoms: Record<string, Tally> = {};

for (const k of readdirSync(taxDir)) {
  if (!statSync(join(taxDir, k)).isDirectory()) continue;
  const t = newTally();
  kingdoms[k] = t;

  let unreadable = 0;
  for (const f of walkFamilies(join(taxDir, k))) {
    t.families++;
    try {
      tallyTree(JSON.parse(readFileSync(f, "utf8")), t);
    } catch {
      unreadable++;
      if (unreadable === 1) console.warn(`WARN  ${f} failed to parse; family files that do not parse are skipped.`);
    }
  }
}

// Roll the per-kingdom tallies into one total.
const total = newTally();
for (const t of Object.values(kingdoms)) {
  total.nodes += t.nodes;
  total.families += t.families;
  for (const [field, counts] of [["sourcedFrom", t.sourcedFrom], ["sourceIds", t.sourceIds]] as const) {
    for (const [k, v] of Object.entries(counts)) total[field][k] = (total[field][k] ?? 0) + v;
  }
}

/** Resolve one id to display metadata, from the manifest where possible. */
function resolveSource(id: string) {
  const alias = ALIASES[id];
  // Alias first, then a manifest row of the same name, then nothing — in that
  // order, so an alias can name the route a source actually arrived by even
  // where a same-named manifest row exists.
  const keys = alias ? alias.datasets : manifest?.[id] ? [id] : [];
  const rows = keys.map((k) => manifest?.[k]).filter(Boolean) as NonNullable<Manifest[string]>[];
  const licences = [...new Set(rows.map((r) => r.licence).filter(Boolean))];
  const appliedDatasets = id === "checklistbank"
    ? Object.keys(manifest ?? {}).filter((k) => k.startsWith("checklistbank-") && manifest![k].status === "applied")
    : keys;

  const inline: Record<string, { name: string; url?: string; licence?: string }> = {
    wikipedia: { name: "English Wikipedia", url: "https://en.wikipedia.org", licence: "CC BY-SA 4.0" },
    wikidata: { name: "Wikidata", url: "https://www.wikidata.org", licence: "CC0" },
    powo: { name: "Plants of the World Online (RBG Kew)", url: "https://powo.science.kew.org", licence: "CC BY" },
    nzpcn: { name: "NZ Plant Conservation Network", url: "https://www.nzpcn.org.nz", licence: "permission-based" },
    websearch: { name: "Mixed — web sources", licence: "mixed; some not open" },
    ollama: { name: "Generated locally (Ollama)", licence: "ours" },
    generated: { name: "Template-generated", licence: "ours" },
    none: { name: "No provenance recorded", licence: undefined },
  };

  const base = rows[0];
  return {
    id,
    name: inline[id]?.name ?? base?.title ?? id,
    url: inline[id]?.url ?? base?.url ?? null,
    identifier: base?.identifier ?? null,
    licence: inline[id]?.licence ?? (licences.length ? licences.join(" / ") : null),
    unresolved: licences.length === 0 && !inline[id],
    datasets: appliedDatasets,
    note: alias?.note ?? null,
  };
}

const ids = new Set([...Object.keys(total.sourcedFrom), ...Object.keys(total.sourceIds)]);
const sources = Object.fromEntries([...ids].sort().map((id) => [id, resolveSource(id)]));

const report = {
  generatedAt: new Date().toISOString(),
  note: "Generated by portal/scripts/aggregateSources.ts — recount with `make sources-report`.",
  totals: { nodes: total.nodes, families: total.families, kingdoms: Object.keys(kingdoms).length },
  kingdoms,
  sources,
};

writeFileSync(outPath, JSON.stringify(report, null, 2) + "\n");

const n = (v: number) => v.toLocaleString("en-US");
console.log(`\nFamilies ${n(total.families)}   nodes ${n(total.nodes)}   kingdoms ${Object.keys(kingdoms).length}`);

for (const [label, counts] of [["sourcedFrom (text & names)", total.sourcedFrom], ["sourceIds (dataset records)", total.sourceIds]] as const) {
  const sum = Object.values(counts).reduce((a, b) => a + b, 0);
  console.log(`\n=== ${label} — ${n(sum)} records ===`);
  for (const [id, count] of Object.entries(counts).sort((a, b) => b[1] - a[1])) {
    const s = sources[id];
    console.log(`  ${id.padEnd(30)} ${n(count).padStart(10)}  ${(s.licence ?? (s.unresolved ? "UNRESOLVED" : "—")).slice(0, 34)}`);
  }
}

const unresolved = Object.values(sources).filter((s) => s.unresolved);
if (unresolved.length) {
  console.warn(`\nWARN  ${unresolved.length} ids carry no licence and are not in the manifest:`);
  console.warn(`      ${unresolved.map((s) => s.id).join(", ")}`);
}
console.log(`\nWrote ${outPath}`);