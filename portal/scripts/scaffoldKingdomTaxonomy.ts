/**
 * scaffoldKingdomTaxonomy.ts
 *
 * Builds portal/data/taxonomy-<kingdom>.json from the GBIF backbone for any
 * kingdom. Walks accepted FAMILY records, fetches accepted species counts,
 * filters by a species-count threshold, and assembles a
 * KINGDOM→PHYLUM→CLASS→ORDER→FAMILY tree (Plantae/Fungi snippet format).
 *
 * Usage:
 *   npx tsx scripts/scaffoldKingdomTaxonomy.ts --kingdom Chromista --key 4 [--min 5]
 *
 * Resumable: caches per-family species counts to /tmp/<kingdom-lower>-family-counts.json
 */
import { writeFileSync, readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const portalRoot = resolve(__dirname, "..");

function arg(name: string, def = ""): string {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : def;
}

const KINGDOM_NAME = arg("kingdom");
const KINGDOM_KEY = parseInt(arg("key"), 10);
const MIN_SPECIES = parseInt(arg("min", "5"), 10);
if (!KINGDOM_NAME || !KINGDOM_KEY) {
  console.error("Usage: scaffoldKingdomTaxonomy.ts --kingdom <Name> --key <gbifKey> [--min 5]");
  process.exit(1);
}
const KLOWER = KINGDOM_NAME.toLowerCase();
const OUT = resolve(portalRoot, `data/taxonomy-${KLOWER}.json`);
const COUNT_CACHE = `/tmp/${KLOWER}-family-counts.json`;

const SEARCH = "https://api.gbif.org/v1/species/search";
const RATE_DELAY = 60;
const DESCRIPTIONS: Record<string, string> = {
  chromista: "Chromista is a kingdom of eukaryotic algae and protists — diatoms, brown algae and kelps, golden algae, water moulds (oomycetes), and foraminifera — mostly characterised by chlorophyll-c plastids acquired through secondary endosymbiosis.",
  protozoa: "Protozoa is a kingdom of single-celled eukaryotes — amoebae, flagellates, ciliates, and slime moulds — that are neither animals, plants, fungi, nor chromists.",
};

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

interface FamilyRec { key: number; family: string; phylum: string | null; class: string | null; order: string | null; numDescendants: number; }

async function fetchJson<T>(url: string): Promise<T> {
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
      if (res.status === 429) { await sleep(3000 * (attempt + 1)); continue; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json() as T;
    } catch (e) {
      if (attempt === 3) throw e;
      await sleep(2000 * (attempt + 1));
    }
  }
  throw new Error("unreachable");
}

async function listFamilies(): Promise<FamilyRec[]> {
  const out: FamilyRec[] = [];
  let offset = 0; const limit = 100;
  for (;;) {
    const url = `${SEARCH}?highertaxonKey=${KINGDOM_KEY}&rank=FAMILY&status=ACCEPTED&limit=${limit}&offset=${offset}`;
    const data = await fetchJson<{ results: FamilyRec[]; endOfRecords: boolean }>(url);
    for (const r of data.results) out.push({ key: r.key, family: r.family, phylum: r.phylum ?? null, class: r.class ?? null, order: r.order ?? null, numDescendants: r.numDescendants ?? 0 });
    console.log(`   families fetched: ${out.length}`);
    if (data.endOfRecords) break;
    offset += limit; await sleep(RATE_DELAY);
  }
  return out;
}

async function speciesCount(familyKey: number): Promise<number> {
  const data = await fetchJson<{ count: number }>(`${SEARCH}?highertaxonKey=${familyKey}&rank=SPECIES&status=ACCEPTED&limit=0`);
  return data.count ?? 0;
}

const up = (s: string) => s.replace(/[^A-Za-z0-9]+/g, "_").toUpperCase();
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

interface Node { id: string; name: string; rank: string; commonName: string; appSlug?: string; speciesCount?: number; notableMembers?: string[]; children?: Node[]; }

async function main() {
  console.log(`🌿 Scaffolding ${KINGDOM_NAME} taxonomy (key=${KINGDOM_KEY}, min species = ${MIN_SPECIES})`);
  console.log("📖 Listing accepted families from GBIF…");
  const families = await listFamilies();
  console.log(`   total accepted families: ${families.length}`);

  const candidates = families.filter(f => f.numDescendants >= MIN_SPECIES && f.phylum && f.class && f.order);
  const skipped = families.filter(f => !f.phylum || !f.class || !f.order).length;
  console.log(`   candidates after numDescendants>=${MIN_SPECIES} & full placement: ${candidates.length}`);
  console.log(`   skipped (missing phylum/class/order placement): ${skipped}`);

  const cache: Record<string, number> = existsSync(COUNT_CACHE) ? JSON.parse(readFileSync(COUNT_CACHE, "utf-8")) : {};
  let done = 0;
  for (const f of candidates) {
    if (cache[f.key] === undefined) {
      cache[f.key] = await speciesCount(f.key);
      if (++done % 25 === 0) { writeFileSync(COUNT_CACHE, JSON.stringify(cache)); console.log(`   species counts: ${done}/${candidates.length} new`); }
      await sleep(RATE_DELAY);
    }
  }
  writeFileSync(COUNT_CACHE, JSON.stringify(cache));

  const kept = candidates.filter(f => (cache[f.key] ?? 0) >= MIN_SPECIES);
  console.log(`   families kept (species>=${MIN_SPECIES}): ${kept.length}`);

  const root: Node = { id: up(KINGDOM_NAME), name: KINGDOM_NAME, rank: "KINGDOM", commonName: KINGDOM_NAME, children: [] };
  const desc = DESCRIPTIONS[KLOWER];
  if (desc) (root as { description?: string }).description = desc;

  const phyla = new Map<string, Node>(), classes = new Map<string, Node>(), orders = new Map<string, Node>();
  for (const f of kept) {
    const pName = f.phylum!, cName = f.class!, oName = f.order!;
    let p = phyla.get(pName);
    if (!p) { p = { id: `PHY_${up(pName)}`, name: pName, rank: "PHYLUM", commonName: pName, children: [] }; phyla.set(pName, p); root.children!.push(p); }
    const cKey = `${pName}|${cName}`;
    let c = classes.get(cKey);
    if (!c) { c = { id: `CLS_${up(cName)}`, name: cName, rank: "CLASS", commonName: cName, children: [] }; classes.set(cKey, c); p.children!.push(c); }
    const oKey = `${cKey}|${oName}`;
    let o = orders.get(oKey);
    if (!o) { o = { id: `ORD_${up(oName)}`, name: oName, rank: "ORDER", commonName: oName, children: [] }; orders.set(oKey, o); c.children!.push(o); }
    o.children!.push({ id: `FAM_${up(f.family)}`, name: f.family, rank: "FAMILY", commonName: f.family, appSlug: slug(f.family), speciesCount: cache[f.key] ?? 0, notableMembers: [] });
  }

  const sortRec = (n: Node) => { n.children?.sort((a, b) => a.name.localeCompare(b.name)); n.children?.forEach(sortRec); };
  sortRec(root);

  writeFileSync(OUT, JSON.stringify(root, null, 2) + "\n");
  const totalSpecies = kept.reduce((s, f) => s + (cache[f.key] ?? 0), 0);
  console.log(`\n✅ Wrote ${OUT}`);
  console.log(`   ${phyla.size} phyla · ${classes.size} classes · ${orders.size} orders · ${kept.length} families · ${totalSpecies} species`);
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
