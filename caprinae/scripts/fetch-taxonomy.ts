import { writeFileSync } from "fs";
import { join } from "path";
import { SHEEP_BREEDS, GOAT_BREEDS, SHEEP_GROUPS, GOAT_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_SHEEP_SCINAME = "Ovis aries";
const DOMESTIC_SHEEP_SYNONYMS = new Set(["Ovis aries", "Ovis gmelini aries", "Ovis ammon aries"]);
export const DOMESTIC_SHEEP_ID = "DOMESTIC_SHEEP";

const DOMESTIC_GOAT_SCINAME = "Capra hircus";
const DOMESTIC_GOAT_SYNONYMS = new Set(["Capra hircus", "Capra aegagrus hircus"]);
export const DOMESTIC_GOAT_ID = "DOMESTIC_GOAT";

const ALL_DOMESTIC_SYNONYMS = new Set([...DOMESTIC_SHEEP_SYNONYMS, ...DOMESTIC_GOAT_SYNONYMS]);

const COMMON_NAMES: Record<string, string> = {
  // Ovis
  "Ovis ammon":              "Argali",
  "Ovis canadensis":         "Bighorn Sheep",
  "Ovis dalli":              "Dall Sheep",
  "Ovis gmelini":            "Mouflon",
  "Ovis musimon":            "European Mouflon",
  "Ovis nivicola":           "Snow Sheep",
  "Ovis vignei":             "Urial",
  // Capra
  "Capra aegagrus":          "Wild Goat",
  "Capra caucasica":         "West Caucasian Tur",
  "Capra cylindricornis":    "East Caucasian Tur",
  "Capra falconeri":         "Markhor",
  "Capra ibex":              "Alpine Ibex",
  "Capra nubiana":           "Nubian Ibex",
  "Capra pyrenaica":         "Spanish Ibex",
  "Capra sibirica":          "Siberian Ibex",
  "Capra walie":             "Walia Ibex",
  // Pseudois
  "Pseudois nayaur":         "Bharal",
  "Pseudois schaeferi":      "Dwarf Blue Sheep",
  // Rupicapra
  "Rupicapra rupicapra":     "Alpine Chamois",
  "Rupicapra pyrenaica":     "Pyrenean Chamois",
  // Ovibos
  "Ovibos moschatus":        "Muskox",
  // Oreamnos
  "Oreamnos americanus":     "Mountain Goat",
  // Tahr
  "Hemitragus jemlahicus":   "Himalayan Tahr",
  "Nilgiritragus hylocrius": "Nilgiri Tahr",
  "Arabitragus jayakari":    "Arabian Tahr",
  // Naemorhedus
  "Naemorhedus baileyi":     "Red Goral",
  "Naemorhedus caudatus":    "Long-tailed Goral",
  "Naemorhedus goral":       "Himalayan Goral",
  "Naemorhedus griseus":     "Chinese Goral",
  // Capricornis
  "Capricornis crispus":        "Japanese Serow",
  "Capricornis milneedwardsii": "Mainland Serow",
  "Capricornis rubidus":        "Red Serow",
  "Capricornis sumatraensis":   "Sumatran Serow",
  "Capricornis swinhoei":       "Taiwan Serow",
  "Capricornis thar":           "Himalayan Serow",
  // Budorcas
  "Budorcas taxicolor":      "Takin",
  // Pantholops
  "Pantholops hodgsonii":    "Chiru",
  // Ammotragus
  "Ammotragus lervia":       "Barbary Sheep",
};

const SUBSPECIES_COMMON_NAMES: Record<string, string> = {
  // Bighorn subspecies
  "Ovis canadensis canadensis": "Rocky Mountain Bighorn",
  "Ovis canadensis nelsoni":    "Desert Bighorn",
  "Ovis canadensis sierra":     "Sierra Nevada Bighorn",
  // Takin subspecies
  "Budorcas taxicolor tibetanus": "Tibetan Takin",
  "Budorcas taxicolor taxicolor": "Mishmi Takin",
  "Budorcas taxicolor bedfordi":  "Golden Takin",
  "Budorcas taxicolor whitei":    "Bhutan Takin",
  // Markhor subspecies
  "Capra falconeri falconeri":    "Astor Markhor",
  "Capra falconeri megaceros":    "Kabul Markhor",
  "Capra falconeri heptneri":     "Bukharan Markhor",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  "Ovis":          "Sheep",
  "Capra":         "Goat",
  "Pseudois":      "Blue Sheep",
  "Rupicapra":     "Chamois",
  "Ovibos":        "Musk Ox",
  "Oreamnos":      "Mountain Goat",
  "Hemitragus":    "Tahr",
  "Arabitragus":   "Tahr",
  "Nilgiritragus": "Tahr",
  "Naemorhedus":   "Goral",
  "Capricornis":   "Serow",
  "Budorcas":      "Takin",
  "Pantholops":    "Chiru",
  "Ammotragus":    "Barbary Sheep",
};

interface ApiRecord {
  id: string;
  usage: {
    id: string;
    parentId?: string;
    status: string;
    extinct: boolean;
    name: {
      scientificName: string;
      rank: string;
    };
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
    r.usage.name.scientificName === name &&
    r.usage.status === "accepted"
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
      ...(SUBSPECIES_COMMON_NAMES[sciName] && { commonName: SUBSPECIES_COMMON_NAMES[sciName] }),
      ...(getLineage(sciName) && { lineage: getLineage(sciName) }),
    });
  }

  // Count subspecies per species
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

  // Inject non-accepted subspecies with well-known common names
  const speciesByName = new Map<string, TaxonNode>();
  for (const node of byId.values()) {
    if (node.rank === "SPECIES") speciesByName.set(node.name, node);
  }
  const acceptedSubspeciesNames = new Set<string>();
  for (const children of childrenMap.values()) {
    for (const c of children) {
      if (c.rank === "SUBSPECIES") acceptedSubspeciesNames.add(c.name);
    }
  }
  let synonymCount = 0;
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status === "accepted") continue;
    if (u.name.rank.toUpperCase() !== "SUBSPECIES") continue;
    const sciName = u.name.scientificName;
    if (acceptedSubspeciesNames.has(sciName)) continue;
    const parts = sciName.split(" ");
    if (parts.length < 3) continue;
    const speciesName = `${parts[0]} ${parts[1]}`;
    const parentSpecies = speciesByName.get(speciesName);
    if (!parentSpecies) continue;
    const siblings = childrenMap.get(parentSpecies.id) ?? [];
    if (siblings.some(c => c.name === sciName)) continue;
    const commonName = SUBSPECIES_COMMON_NAMES[sciName];
    if (!commonName) continue;
    siblings.push({
      id: `synonym-${r.id}`,
      name: sciName,
      rank: "SUBSPECIES",
      accepted: false,
      commonName,
      ...(getLineage(sciName) && { lineage: getLineage(sciName) }),
    });
    childrenMap.set(parentSpecies.id, siblings);
    synonymCount++;
  }
  console.log(`Added ${synonymCount} non-accepted subspecies`);

  function attach(node: TaxonNode): TaxonNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(attach).sort((a, b) => a.name.localeCompare(b.name));
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Caprinae root not found: ${rootId}`);
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

function injectDomesticSheep(tree: TaxonNode): void {
  const ovisGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Ovis");
  if (!ovisGenus) {
    console.warn("Ovis genus not found — skipping domestic sheep injection");
    return;
  }

  const sheepNode: TaxonNode = {
    id: DOMESTIC_SHEEP_ID,
    name: DOMESTIC_SHEEP_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Sheep",
    lineage: "Sheep",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };

  ovisGenus.children = [...(ovisGenus.children ?? []), sheepNode].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic sheep node into Ovis genus");
}

function injectDomesticGoat(tree: TaxonNode): void {
  const capraGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Capra");
  if (!capraGenus) {
    console.warn("Capra genus not found — skipping domestic goat injection");
    return;
  }

  const goatNode: TaxonNode = {
    id: DOMESTIC_GOAT_ID,
    name: DOMESTIC_GOAT_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Goat",
    lineage: "Goat",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };

  capraGenus.children = [...(capraGenus.children ?? []), goatNode].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic goat node into Capra genus");
}

function injectSheepBreeds(tree: TaxonNode): void {
  const sheepNode = findNode(tree, n => n.id === DOMESTIC_SHEEP_ID);
  if (!sheepNode) {
    console.warn("Domestic sheep node not found — skipping sheep breed injection");
    return;
  }

  sheepNode.children = SHEEP_GROUPS.map(group => {
    const groupBreeds = SHEEP_BREEDS.filter(b => b.group === group);
    return {
      id: `sheep-breed-group-${group.toLowerCase()}`,
      name: group,
      rank: "BREED_GROUP",
      lineage: "Sheep",
      children: groupBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Sheep",
        })),
    };
  });

  console.log(`Injected ${SHEEP_BREEDS.length} sheep breeds in ${SHEEP_GROUPS.length} groups`);
}

function injectGoatBreeds(tree: TaxonNode): void {
  const goatNode = findNode(tree, n => n.id === DOMESTIC_GOAT_ID);
  if (!goatNode) {
    console.warn("Domestic goat node not found — skipping goat breed injection");
    return;
  }

  goatNode.children = GOAT_GROUPS.map(group => {
    const groupBreeds = GOAT_BREEDS.filter(b => b.group === group);
    return {
      id: `goat-breed-group-${group.toLowerCase()}`,
      name: group,
      rank: "BREED_GROUP",
      lineage: "Goat",
      children: groupBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Goat",
        })),
    };
  });

  console.log(`Injected ${GOAT_BREEDS.length} goat breeds in ${GOAT_GROUPS.length} groups`);
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
  // COL 3LR uses "Caprini" (tribe) as the accepted name for what is commonly called Caprinae
  console.log("Fetching Caprinae taxonomy from COL ChecklistBank...");
  const CAPRINAE_ID = await findTaxonId("Caprini", "tribe");
  const records = await fetchAll(CAPRINAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, CAPRINAE_ID);
  injectDomesticSheep(tree);
  injectDomesticGoat(tree);
  injectSheepBreeds(tree);
  injectGoatBreeds(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const topLevel = tree.children?.map(c => `${c.commonName ?? c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Top level: ${topLevel}`);

  const outPath = join(import.meta.dirname, "../src/data/caprinae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
