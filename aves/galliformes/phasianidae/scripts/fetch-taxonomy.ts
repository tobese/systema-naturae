import { writeFileSync } from "fs";
import { join } from "path";
import { CHICKEN_BREEDS, TURKEY_BREEDS, CHICKEN_GROUPS, TURKEY_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_CHICKEN_SCINAME = "Gallus gallus domesticus";
const DOMESTIC_CHICKEN_SYNONYMS = new Set([
  "Gallus domesticus",
  "Gallus gallus domesticus",
  "Gallus gallus f. domestica",
]);
export const DOMESTIC_CHICKEN_ID = "DOMESTIC_CHICKEN";

const DOMESTIC_TURKEY_SCINAME = "Meleagris gallopavo f. domestica";
const DOMESTIC_TURKEY_SYNONYMS = new Set([
  "Meleagris gallopavo domestica",
  "Meleagris gallopavo f. domestica",
  "Meleagris domestica",
]);
export const DOMESTIC_TURKEY_ID = "DOMESTIC_TURKEY";

const ALL_DOMESTIC_SYNONYMS = new Set([...DOMESTIC_CHICKEN_SYNONYMS, ...DOMESTIC_TURKEY_SYNONYMS]);

const COMMON_NAMES: Record<string, string> = {
  // Gallus
  "Gallus gallus":          "Red Junglefowl",
  "Gallus lafayettii":      "Sri Lanka Junglefowl",
  "Gallus sonneratii":      "Grey Junglefowl",
  "Gallus varius":          "Green Junglefowl",
  // Meleagris
  "Meleagris gallopavo":    "Wild Turkey",
  "Meleagris ocellata":     "Ocellated Turkey",
  // Pavo / Afropavo
  "Pavo cristatus":         "Indian Peafowl",
  "Pavo muticus":           "Green Peafowl",
  "Afropavo congensis":     "Congo Peafowl",
  // Phasianus
  "Phasianus colchicus":    "Common Pheasant",
  "Phasianus versicolor":   "Green Pheasant",
  // Chrysolophus
  "Chrysolophus pictus":       "Golden Pheasant",
  "Chrysolophus amherstiae":   "Lady Amherst's Pheasant",
  // Lophura
  "Lophura leucomelanos":   "Kalij Pheasant",
  "Lophura nycthemera":     "Silver Pheasant",
  "Lophura edwardsi":       "Edwards's Pheasant",
  // Syrmaticus
  "Syrmaticus reevesii":    "Reeves's Pheasant",
  "Syrmaticus ellioti":     "Elliot's Pheasant",
  // Argusianus / Rheinardia
  "Argusianus argus":       "Great Argus",
  "Rheinardia ocellata":    "Crested Argus",
  // Tragopan
  "Tragopan temminckii":    "Temminck's Tragopan",
  "Tragopan satyra":        "Satyr Tragopan",
  // Perdix
  "Perdix perdix":          "Grey Partridge",
  "Perdix dauurica":        "Daurian Partridge",
  "Perdix hodgsoniae":      "Tibetan Partridge",
  // Alectoris
  "Alectoris chukar":       "Chukar",
  "Alectoris graeca":       "Rock Partridge",
  "Alectoris rufa":         "Red-legged Partridge",
  "Alectoris barbara":      "Barbary Partridge",
  // Coturnix
  "Coturnix coturnix":      "Common Quail",
  "Coturnix japonica":      "Japanese Quail",
  "Coturnix chinensis":     "King Quail",
  // Lagopus
  "Lagopus lagopus":        "Willow Ptarmigan",
  "Lagopus muta":           "Rock Ptarmigan",
  "Lagopus leucura":        "White-tailed Ptarmigan",
  // Tetrao
  "Tetrao urogallus":       "Western Capercaillie",
  "Tetrao parvirostris":    "Black-billed Capercaillie",
  // Lyrurus
  "Lyrurus tetrix":         "Black Grouse",
  "Lyrurus mlokosiewiczi":  "Caucasian Grouse",
  // Bonasa
  "Bonasa umbellus":        "Ruffed Grouse",
  // Dendragapus
  "Dendragapus obscurus":   "Dusky Grouse",
  "Dendragapus fuliginosus":"Sooty Grouse",
  // Tetraogallus
  "Tetraogallus himalayensis": "Himalayan Snowcock",
  "Tetraogallus tibetanus":    "Tibetan Snowcock",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  "Gallus":        "Junglefowl",
  "Meleagris":     "Turkey",
  "Pavo":          "Peacock",
  "Afropavo":      "Peacock",
  "Phasianus":     "Pheasant",
  "Chrysolophus":  "Pheasant",
  "Syrmaticus":    "Pheasant",
  "Lophura":       "Pheasant",
  "Polyplectron":  "Pheasant",
  "Argusianus":    "Pheasant",
  "Rheinardia":    "Pheasant",
  "Tragopan":      "Pheasant",
  "Ithaginis":     "Pheasant",
  "Catreus":       "Pheasant",
  "Crossoptilon":  "Pheasant",
  "Pucrasia":      "Pheasant",
  "Lophocroa":     "Pheasant",
  "Lophophorus":   "Pheasant",
  "Coturnix":      "Quail",
  "Synoicus":      "Quail",
  "Excalfactoria": "Quail",
  "Perdix":        "Partridge",
  "Alectoris":     "Partridge",
  "Francolinus":   "Partridge",
  "Peliperdix":    "Partridge",
  "Pternistis":    "Partridge",
  "Arborophila":   "Partridge",
  "Bambusicola":   "Partridge",
  "Campocolinus":  "Partridge",
  "Scleroptila":   "Partridge",
  "Ammoperdix":    "Partridge",
  "Caloperdix":    "Partridge",
  "Lagopus":       "Grouse",
  "Tetrao":        "Grouse",
  "Lyrurus":       "Grouse",
  "Tetrastes":     "Grouse",
  "Dendragapus":   "Grouse",
  "Bonasa":        "Grouse",
  "Canachites":    "Grouse",
  "Falcipennis":   "Grouse",
  "Centrocercus":  "Grouse",
  "Tympanuchus":   "Grouse",
  "Galloperdix":   "Spurfowl",
  "Lerwa":         "Spurfowl",
  "Ophrysia":      "Spurfowl",
  "Tetraophasis":  "Spurfowl",
  "Tetraogallus":  "Spurfowl",
};

interface ApiRecord {
  id: string;
  usage: {
    id: string;
    parentId?: string;
    status: string;
    extinct: boolean;
    name: { scientificName: string; rank: string };
  };
}

export interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  lineage?: string;
  origin?: string;
  subspeciesCount?: number;
  continents?: string[];
  accepted?: boolean;
  children?: TaxonNode[];
}

async function findTaxonId(name: string, rank: string): Promise<string> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?q=${encodeURIComponent(name)}&rank=${rank}&limit=20`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[] };
  const match = json.result.find(r =>
    r.usage.name.scientificName === name && r.usage.status === "accepted"
  );
  if (!match) throw new Error(`${name} not found in COL dataset ${DATASET}`);
  console.log(`Found ${name} → ID: ${match.id}`);
  return match.id;
}

async function fetchPage(rootId: string, offset: number, limit = 500): Promise<{ records: ApiRecord[]; total: number }> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?TAXON_ID=${rootId}&limit=${limit}&offset=${offset}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[]; total: number };
  return { records: json.result, total: json.total };
}

async function fetchAll(rootId: string): Promise<ApiRecord[]> {
  const records: ApiRecord[] = [];
  const { records: first, total } = await fetchPage(rootId, 0);
  records.push(...first);
  console.log(`Total: ${total} taxa, batch 1: ${first.length}`);
  for (let offset = first.length; offset < total; offset += 500) {
    const { records: page } = await fetchPage(rootId, offset);
    records.push(...page);
    console.log(`  fetched ${records.length}/${total}`);
  }
  return records;
}

function getLineage(sciName: string): string | undefined {
  const genus = sciName.split(" ")[0];
  return LINEAGE_BY_GENUS[genus];
}

function buildTree(records: ApiRecord[], rootId: string): TaxonNode {
  const byId = new Map<string, TaxonNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
    if (ALL_DOMESTIC_SYNONYMS.has(u.name.scientificName)) continue;
    const sciName = u.name.scientificName;
    const rank = u.name.rank.toUpperCase();
    byId.set(r.id, {
      id: r.id,
      name: sciName,
      rank,
      ...(COMMON_NAMES[sciName] && { commonName: COMMON_NAMES[sciName] }),
      ...(getLineage(sciName) && { lineage: getLineage(sciName) }),
    });
  }

  const subspeciesCounts = new Map<string, number>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (ALL_DOMESTIC_SYNONYMS.has(u.name.scientificName)) continue;
    if (u.name.rank.toUpperCase() === "SUBSPECIES" && u.parentId) {
      subspeciesCounts.set(u.parentId, (subspeciesCounts.get(u.parentId) ?? 0) + 1);
    }
  }
  for (const [id, count] of subspeciesCounts) {
    const node = byId.get(id);
    if (node) node.subspeciesCount = count;
  }

  const childrenMap = new Map<string, TaxonNode[]>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (ALL_DOMESTIC_SYNONYMS.has(u.name.scientificName)) continue;
    if (!u.parentId) continue;
    const node = byId.get(r.id);
    if (!node) continue;
    const siblings = childrenMap.get(u.parentId) ?? [];
    siblings.push(node);
    childrenMap.set(u.parentId, siblings);
  }

  function attach(node: TaxonNode): TaxonNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(attach).sort((a, b) => a.name.localeCompare(b.name));
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Phasianidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

function findNode(root: TaxonNode, predicate: (n: TaxonNode) => boolean): TaxonNode | undefined {
  if (predicate(root)) return root;
  for (const child of root.children ?? []) {
    const found = findNode(child, predicate);
    if (found) return found;
  }
}

function injectDomesticChicken(tree: TaxonNode): void {
  const gallusGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Gallus");
  if (!gallusGenus) { console.warn("Gallus not found"); return; }
  const node: TaxonNode = {
    id: DOMESTIC_CHICKEN_ID,
    name: DOMESTIC_CHICKEN_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Chicken",
    lineage: "Junglefowl",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };
  gallusGenus.children = [...(gallusGenus.children ?? []), node].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic chicken into Gallus");
}

function injectDomesticTurkey(tree: TaxonNode): void {
  const meleagrisGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Meleagris");
  if (!meleagrisGenus) { console.warn("Meleagris not found"); return; }
  const node: TaxonNode = {
    id: DOMESTIC_TURKEY_ID,
    name: DOMESTIC_TURKEY_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Turkey",
    lineage: "Turkey",
    continents: ["North America", "South America", "Europe", "Asia"],
  };
  meleagrisGenus.children = [...(meleagrisGenus.children ?? []), node].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic turkey into Meleagris");
}

function injectChickenBreeds(tree: TaxonNode): void {
  const chickenNode = findNode(tree, n => n.id === DOMESTIC_CHICKEN_ID);
  if (!chickenNode) { console.warn("Domestic chicken not found"); return; }
  chickenNode.children = CHICKEN_GROUPS.map(group => ({
    id: `chicken-breed-group-${group.toLowerCase().replace(/ /g, "-")}`,
    name: group,
    rank: "BREED_GROUP",
    lineage: "Junglefowl",
    children: CHICKEN_BREEDS
      .filter(b => b.group === group)
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(b => ({ id: b.id, name: b.name, rank: "BREED", origin: b.origin, lineage: "Junglefowl" })),
  }));
  console.log(`Injected ${CHICKEN_BREEDS.length} chicken breeds`);
}

function injectTurkeyBreeds(tree: TaxonNode): void {
  const turkeyNode = findNode(tree, n => n.id === DOMESTIC_TURKEY_ID);
  if (!turkeyNode) { console.warn("Domestic turkey not found"); return; }
  turkeyNode.children = TURKEY_GROUPS.map(group => ({
    id: `turkey-breed-group-${group.toLowerCase()}`,
    name: group,
    rank: "BREED_GROUP",
    lineage: "Turkey",
    children: TURKEY_BREEDS
      .filter(b => b.group === group)
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(b => ({ id: b.id, name: b.name, rank: "BREED", origin: b.origin, lineage: "Turkey" })),
  }));
  console.log(`Injected ${TURKEY_BREEDS.length} turkey breeds`);
}

function injectRanges(tree: TaxonNode): void {
  let count = 0;
  function walk(node: TaxonNode): void {
    if (node.rank === "SPECIES" && SPECIES_RANGES[node.name]) {
      node.continents = SPECIES_RANGES[node.name];
      count++;
    }
    for (const child of node.children ?? []) walk(child);
  }
  walk(tree);
  console.log(`Injected range data for ${count} species`);
}

async function main() {
  console.log("Fetching Phasianidae taxonomy from COL ChecklistBank...");
  const PHASIANIDAE_ID = await findTaxonId("Phasianidae", "family");
  const records = await fetchAll(PHASIANIDAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, PHASIANIDAE_ID);
  injectDomesticChicken(tree);
  injectDomesticTurkey(tree);
  injectChickenBreeds(tree);
  injectTurkeyBreeds(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const outPath = join(import.meta.dirname, "../src/data/phasianidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
