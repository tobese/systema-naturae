import { writeFileSync } from "fs";
import { join } from "path";
import { BREEDS, AKC_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_DOG_SCINAME = "Canis lupus familiaris";
const DOMESTIC_DOG_SYNONYMS = new Set(["Canis lupus familiaris", "Canis familiaris"]);
export const DOMESTIC_DOG_ID = "DOMESTIC_DOG";

const COMMON_NAMES: Record<string, string> = {
  "Canis lupus":               "Gray Wolf",
  "Canis latrans":             "Coyote",
  "Canis aureus":              "Golden Jackal",
  "Canis lupaster":            "African Wolf",
  "Canis lycaon":              "Eastern Wolf",
  "Canis rufus":               "Red Wolf",
  "Canis simensis":            "Ethiopian Wolf",
  "Canis adustus":             "Side-striped Jackal",
  "Canis mesomelas":           "Black-backed Jackal",
  // COL 2024 reclassifies African jackals to Lupulella
  "Lupulella adustus":         "Side-striped Jackal",
  "Lupulella mesomelas":       "Black-backed Jackal",
  "Cuon alpinus":              "Dhole",
  "Lycaon pictus":             "African Wild Dog",
  "Vulpes vulpes":             "Red Fox",
  "Vulpes lagopus":            "Arctic Fox",
  "Vulpes zerda":              "Fennec Fox",
  "Vulpes corsac":             "Corsac Fox",
  "Vulpes bengalensis":        "Bengal Fox",
  "Vulpes cana":               "Blanford's Fox",
  "Vulpes rueppellii":         "Rüppell's Fox",
  "Vulpes pallida":            "Pale Fox",
  "Vulpes chama":              "Cape Fox",
  "Vulpes macrotis":           "Kit Fox",
  "Vulpes velox":              "Swift Fox",
  "Urocyon cinereoargenteus":  "Gray Fox",
  "Urocyon littoralis":        "Island Fox",
  "Otocyon megalotis":         "Bat-eared Fox",
  "Lycalopex culpaeus":        "Culpeo",
  "Lycalopex griseus":         "South American Gray Fox",
  "Lycalopex fulvipes":        "Darwin's Fox",
  "Lycalopex gymnocercus":     "Pampas Fox",
  "Lycalopex sechurae":        "Sechuran Fox",
  "Lycalopex vetulus":         "Hoary Fox",
  "Atelocynus microtis":       "Short-eared Dog",
  "Cerdocyon thous":           "Crab-eating Fox",
  "Chrysocyon brachyurus":     "Maned Wolf",
  "Speothos venaticus":        "Bush Dog",
  "Nyctereutes procyonoides":  "Raccoon Dog",
};

const SUBSPECIES_COMMON_NAMES: Record<string, string> = {
  "Canis lupus lupus":          "Eurasian Wolf",
  "Canis lupus arctos":         "Arctic Wolf",
  "Canis lupus baileyi":        "Mexican Wolf",
  "Canis lupus signatus":       "Iberian Wolf",
  "Canis lupus italicus":       "Italian Wolf",
  "Canis lupus pallipes":       "Indian Wolf",
  "Canis lupus albus":          "Tundra Wolf",
  "Canis lupus nubilus":        "Great Plains Wolf",
  "Canis lupus occidentalis":   "Northwestern Wolf",
  "Canis lupus arabs":          "Arabian Wolf",
  "Canis lupus chanco":         "Tibetan Wolf",
  "Canis lupus columbianus":    "British Columbia Wolf",
  "Canis lupus cubanensis":     "Cuban Wolf",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Canis:       "Wolf",
  Cuon:        "Wolf",
  Lycaon:      "Wolf",
  Lupulella:   "Wolf",   // African jackals (COL 2024 reclassification)
  Dusicyon:    "South American",  // Falkland Islands wolf
  Vulpes:      "Fox",
  Urocyon:     "Fox",
  Otocyon:     "Fox",
  Lycalopex:   "South American",
  Atelocynus:  "South American",
  Cerdocyon:   "South American",
  Chrysocyon:  "South American",
  Speothos:    "South American",
  Nyctereutes: "Raccoon dog",
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

async function findFamilyId(familyName: string): Promise<string> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?q=${encodeURIComponent(familyName)}&rank=family&limit=20`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[] };
  const match = json.result.find(r =>
    r.usage.name.scientificName === familyName &&
    r.usage.status === "accepted"
  );
  if (!match) throw new Error(`${familyName} not found in COL dataset ${DATASET}`);
  console.log(`Found ${familyName} → ID: ${match.id}`);
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

function buildTree(records: ApiRecord[], rootId: string): TaxonNode {
  const byId = new Map<string, TaxonNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
    // Exclude domestic dog names — injected separately as a species-level node
    if (DOMESTIC_DOG_SYNONYMS.has(u.name.scientificName)) continue;
    const sciName = u.name.scientificName;
    const rank = u.name.rank.toUpperCase();
    const genus = sciName.split(" ")[0];
    byId.set(r.id, {
      id: r.id,
      name: sciName,
      rank,
      ...(COMMON_NAMES[sciName] && { commonName: COMMON_NAMES[sciName] }),
      ...(SUBSPECIES_COMMON_NAMES[sciName] && { commonName: SUBSPECIES_COMMON_NAMES[sciName] }),
      ...(LINEAGE_BY_GENUS[genus] && { lineage: LINEAGE_BY_GENUS[genus] }),
    });
  }

  // Count subspecies per species (excluding domestic dog)
  const subspeciesCounts = new Map<string, number>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (DOMESTIC_DOG_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_DOG_SYNONYMS.has(u.name.scientificName)) continue;
    if (!u.parentId) continue;
    const node = byId.get(r.id);
    if (!node) continue;
    const siblings = childrenMap.get(u.parentId) ?? [];
    siblings.push(node);
    childrenMap.set(u.parentId, siblings);
  }

  // Inject non-accepted subspecies that have well-known common names
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
    const genus = parts[0];
    siblings.push({
      id: `synonym-${r.id}`,
      name: sciName,
      rank: "SUBSPECIES",
      accepted: false,
      commonName,
      ...(LINEAGE_BY_GENUS[genus] && { lineage: LINEAGE_BY_GENUS[genus] }),
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
  if (!root) throw new Error(`Canidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

function injectDomesticDog(tree: TaxonNode): void {
  function findNode(node: TaxonNode, predicate: (n: TaxonNode) => boolean): TaxonNode | undefined {
    if (predicate(node)) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, predicate);
      if (found) return found;
    }
  }

  const canisGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Canis");
  if (!canisGenus) {
    console.warn("Canis genus not found — skipping domestic dog injection");
    return;
  }

  const dogNode: TaxonNode = {
    id: DOMESTIC_DOG_ID,
    name: DOMESTIC_DOG_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Dog",
    lineage: "Wolf",
    continents: ["North America", "Europe", "Asia", "Africa", "South America"],
  };

  canisGenus.children = [...(canisGenus.children ?? []), dogNode].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic dog node into Canis genus");
}

function injectBreeds(tree: TaxonNode): void {
  function findNode(node: TaxonNode, id: string): TaxonNode | undefined {
    if (node.id === id) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, id);
      if (found) return found;
    }
  }

  const dogNode = findNode(tree, DOMESTIC_DOG_ID);
  if (!dogNode) {
    console.warn("Domestic dog node not found — skipping breed injection");
    return;
  }

  dogNode.children = AKC_GROUPS.map(group => {
    const groupBreeds = BREEDS.filter(b => b.group === group);
    return {
      id: `breed-group-${group.toLowerCase().replace(/[^a-z]/g, "-")}`,
      name: group,
      rank: "BREED_GROUP",
      lineage: "Wolf",
      children: groupBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Wolf",
        })),
    };
  });

  console.log(`Injected ${BREEDS.length} breeds in ${AKC_GROUPS.length} AKC groups under domestic dog`);
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
  console.log("Fetching Canidae taxonomy from COL ChecklistBank...");
  const CANIDAE_ID = await findFamilyId("Canidae");
  const records = await fetchAll(CANIDAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, CANIDAE_ID);
  injectDomesticDog(tree);
  injectBreeds(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const subfamilies = tree.children?.map(c => `${c.commonName ?? c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Subfamilies: ${subfamilies}`);

  const outPath = join(import.meta.dirname, "../src/data/canidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
