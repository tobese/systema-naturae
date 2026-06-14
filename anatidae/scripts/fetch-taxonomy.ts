import { writeFileSync } from "fs";
import { join } from "path";
import { DUCK_BREEDS, GOOSE_BREEDS, DUCK_GROUPS, GOOSE_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_DUCK_SCINAME = "Anas platyrhynchos domesticus";
const DOMESTIC_DUCK_SYNONYMS = new Set([
  "Anas domesticus",
  "Anas platyrhynchos domestica",
  "Anas platyrhynchos domesticus",
  "Anas platyrhynchos f. domestica",
]);
export const DOMESTIC_DUCK_ID = "DOMESTIC_DUCK";

const DOMESTIC_GOOSE_SCINAME = "Anser anser domesticus";
const DOMESTIC_GOOSE_SYNONYMS = new Set([
  "Anser domesticus",
  "Anser anser domesticus",
  "Anser anser f. domestica",
]);
export const DOMESTIC_GOOSE_ID = "DOMESTIC_GOOSE";

const ALL_DOMESTIC_SYNONYMS = new Set([...DOMESTIC_DUCK_SYNONYMS, ...DOMESTIC_GOOSE_SYNONYMS]);

const COMMON_NAMES: Record<string, string> = {
  // Cygnus — swans
  "Cygnus olor":             "Mute Swan",
  "Cygnus cygnus":           "Whooper Swan",
  "Cygnus columbianus":      "Tundra Swan",
  "Cygnus buccinator":       "Trumpeter Swan",
  "Cygnus atratus":          "Black Swan",
  "Cygnus melanocoryphus":   "Black-necked Swan",
  "Coscoroba coscoroba":     "Coscoroba Swan",
  // Anser — grey geese
  "Anser anser":             "Greylag Goose",
  "Anser brachyrhynchus":    "Pink-footed Goose",
  "Anser cygnoides":         "Swan Goose",
  "Anser fabalis":           "Bean Goose",
  "Anser albifrons":         "Greater White-fronted Goose",
  "Anser erythropus":        "Lesser White-fronted Goose",
  "Anser indicus":           "Bar-headed Goose",
  "Anser caerulescens":      "Snow Goose",
  "Anser rossii":            "Ross's Goose",
  // Branta — black geese
  "Branta canadensis":       "Canada Goose",
  "Branta hutchinsii":       "Cackling Goose",
  "Branta bernicla":         "Brent Goose",
  "Branta leucopsis":        "Barnacle Goose",
  "Branta ruficollis":       "Red-breasted Goose",
  // Alopochen
  "Alopochen aegyptiaca":    "Egyptian Goose",
  // Tadorna
  "Tadorna tadorna":         "Common Shelduck",
  "Tadorna ferruginea":      "Ruddy Shelduck",
  // Aix
  "Aix galericulata":        "Mandarin Duck",
  "Aix sponsa":              "Wood Duck",
  // Cairina
  "Cairina moschata":        "Muscovy Duck",
  // Anas — dabbling ducks
  "Anas platyrhynchos":      "Mallard",
  "Anas acuta":              "Northern Pintail",
  "Anas crecca":             "Eurasian Teal",
  "Anas clypeata":           "Northern Shoveler",
  "Anas strepera":           "Gadwall",
  "Anas penelope":           "Eurasian Wigeon",
  "Anas americana":          "American Wigeon",
  "Anas rubripes":           "American Black Duck",
  // Aythya — diving ducks
  "Aythya fuligula":         "Tufted Duck",
  "Aythya ferina":           "Common Pochard",
  "Aythya marila":           "Greater Scaup",
  "Aythya affinis":          "Lesser Scaup",
  "Aythya valisineria":      "Canvasback",
  // Somateria — eider
  "Somateria mollissima":    "Common Eider",
  "Somateria spectabilis":   "King Eider",
  // Mergus
  "Mergus merganser":        "Common Merganser",
  "Mergus serrator":         "Red-breasted Merganser",
  "Mergus squamatus":        "Scaly-sided Merganser",
  // Oxyura — stifftail
  "Oxyura jamaicensis":      "Ruddy Duck",
  "Oxyura leucocephala":     "White-headed Duck",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  "Cygnus":       "Swan",
  "Coscoroba":    "Swan",
  "Anser":        "Goose",
  "Chen":         "Goose",
  "Branta":       "Goose",
  "Alopochen":    "Goose",
  "Chloephaga":   "Goose",
  "Neochen":      "Goose",
  "Anas":         "Dabbling Duck",
  "Spatula":      "Dabbling Duck",
  "Mareca":       "Dabbling Duck",
  "Sibirionetta": "Dabbling Duck",
  "Aythya":       "Diving Duck",
  "Netta":        "Diving Duck",
  "Somateria":    "Eider",
  "Polysticta":   "Eider",
  "Mergus":       "Merganser",
  "Lophodytes":   "Merganser",
  "Mergellus":    "Merganser",
  "Aix":          "Perching Duck",
  "Cairina":      "Perching Duck",
  "Asarcornis":   "Perching Duck",
  "Pteronetta":   "Perching Duck",
  "Nettapus":     "Perching Duck",
  "Oxyura":       "Stifftail",
  "Biziura":      "Stifftail",
  "Nomonyx":      "Stifftail",
  "Heteronetta":  "Stifftail",
  "Tadorna":      "Shelduck",
  "Radjah":       "Shelduck",
  "Casarca":      "Shelduck",
  "Callonetta":   "Teal/Other",
  "Amazonetta":   "Teal/Other",
  "Lophonetta":   "Teal/Other",
  "Speculanas":   "Teal/Other",
  "Tachyeres":    "Teal/Other",
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
  if (!root) throw new Error(`Anatidae root not found: ${rootId}`);
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

function injectDomesticDuck(tree: TaxonNode): void {
  const anasGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Anas");
  if (!anasGenus) { console.warn("Anas not found"); return; }
  const node: TaxonNode = {
    id: DOMESTIC_DUCK_ID,
    name: DOMESTIC_DUCK_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Duck",
    lineage: "Dabbling Duck",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };
  anasGenus.children = [...(anasGenus.children ?? []), node].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic duck into Anas");
}

function injectDomesticGoose(tree: TaxonNode): void {
  const anserGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Anser");
  if (!anserGenus) { console.warn("Anser not found"); return; }
  const node: TaxonNode = {
    id: DOMESTIC_GOOSE_ID,
    name: DOMESTIC_GOOSE_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Goose",
    lineage: "Goose",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };
  anserGenus.children = [...(anserGenus.children ?? []), node].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic goose into Anser");
}

function injectDuckBreeds(tree: TaxonNode): void {
  const duckNode = findNode(tree, n => n.id === DOMESTIC_DUCK_ID);
  if (!duckNode) { console.warn("Domestic duck not found"); return; }
  duckNode.children = DUCK_GROUPS.map(group => ({
    id: `duck-breed-group-${group.toLowerCase().replace(/ /g, "-")}`,
    name: group,
    rank: "BREED_GROUP",
    lineage: "Dabbling Duck",
    children: DUCK_BREEDS
      .filter(b => b.group === group)
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(b => ({ id: b.id, name: b.name, rank: "BREED", origin: b.origin, lineage: "Dabbling Duck" })),
  }));
  console.log(`Injected ${DUCK_BREEDS.length} duck breeds`);
}

function injectGooseBreeds(tree: TaxonNode): void {
  const gooseNode = findNode(tree, n => n.id === DOMESTIC_GOOSE_ID);
  if (!gooseNode) { console.warn("Domestic goose not found"); return; }
  gooseNode.children = GOOSE_GROUPS.map(group => ({
    id: `goose-breed-group-${group.toLowerCase()}`,
    name: group,
    rank: "BREED_GROUP",
    lineage: "Goose",
    children: GOOSE_BREEDS
      .filter(b => b.group === group)
      .sort((a, b) => a.name.localeCompare(b.name))
      .map(b => ({ id: b.id, name: b.name, rank: "BREED", origin: b.origin, lineage: "Goose" })),
  }));
  console.log(`Injected ${GOOSE_BREEDS.length} goose breeds`);
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
  console.log("Fetching Anatidae taxonomy from COL ChecklistBank...");
  const ANATIDAE_ID = await findTaxonId("Anatidae", "family");
  const records = await fetchAll(ANATIDAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, ANATIDAE_ID);
  injectDomesticDuck(tree);
  injectDomesticGoose(tree);
  injectDuckBreeds(tree);
  injectGooseBreeds(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const topLevel = tree.children?.map(c => `${c.commonName ?? c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Top level: ${topLevel}`);

  const outPath = join(import.meta.dirname, "../src/data/anatidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
