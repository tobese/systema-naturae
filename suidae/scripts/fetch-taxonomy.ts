import { writeFileSync } from "fs";
import { join } from "path";
import { PIG_BREEDS, PIG_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_PIG_SCINAME = "Sus scrofa domesticus";
const DOMESTIC_PIG_SYNONYMS = new Set([
  "Sus domesticus",
  "Sus scrofa domesticus",
  "Sus scrofa domestica",
  "Sus scrofa f. domestica",
]);
export const DOMESTIC_PIG_ID = "DOMESTIC_PIG";

const COMMON_NAMES: Record<string, string> = {
  // Sus
  "Sus ahoenobarbus":    "Palawan Bearded Pig",
  "Sus scrofa":          "Wild Boar",
  "Sus barbatus":        "Bornean Bearded Pig",
  "Sus cebifrons":       "Visayan Warty Pig",
  "Sus celebensis":      "Celebes Warty Pig",
  "Sus heureni":         "Flores Warty Pig",
  "Sus oliveri":         "Mindoro Warty Pig",
  "Sus philippensis":    "Philippine Warty Pig",
  "Sus verrucosus":      "Javan Warty Pig",
  // Porcula
  "Porcula salvania":    "Pygmy Hog",
  // Babyrousa
  "Babyrousa babyrussa":   "Buru Babirusa",
  "Babyrousa celebensis":  "Sulawesi Babirusa",
  "Babyrousa togeanensis": "Togian Babirusa",
  // Phacochoerus
  "Phacochoerus africanus":   "Common Warthog",
  "Phacochoerus aethiopicus": "Desert Warthog",
  // Hylochoerus
  "Hylochoerus meinertzhageni": "Giant Forest Hog",
  // Potamochoerus
  "Potamochoerus larvatus": "Bushpig",
  "Potamochoerus porcus":   "Red River Hog",
};

const SUBSPECIES_COMMON_NAMES: Record<string, string> = {
  "Sus scrofa scrofa":       "Eurasian Wild Boar",
  "Sus scrofa cristatus":    "Indian Wild Boar",
  "Sus scrofa moupinensis":  "Moupin Wild Boar",
  "Sus scrofa vittatus":     "Sunda Wild Boar",
  "Sus scrofa affinis":      "Ceylon Wild Boar",
  "Sus scrofa riukiuanus":   "Ryukyu Wild Boar",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  "Sus":          "Pig",
  "Porcula":      "Pygmy Hog",
  "Babyrousa":    "Babirusa",
  "Phacochoerus": "Warthog",
  "Hylochoerus":  "Forest Hog",
  "Potamochoerus":"Bushpig",
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
    if (DOMESTIC_PIG_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_PIG_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_PIG_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_PIG_SYNONYMS.has(sciName)) continue;
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
  if (!root) throw new Error(`Suidae root not found: ${rootId}`);
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

function injectDomesticPig(tree: TaxonNode): void {
  const susGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Sus");
  if (!susGenus) {
    console.warn("Sus genus not found — skipping domestic pig injection");
    return;
  }

  const pigNode: TaxonNode = {
    id: DOMESTIC_PIG_ID,
    name: DOMESTIC_PIG_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Pig",
    lineage: "Pig",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };

  susGenus.children = [...(susGenus.children ?? []), pigNode].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic pig node into Sus genus");
}

function injectPigBreeds(tree: TaxonNode): void {
  const pigNode = findNode(tree, n => n.id === DOMESTIC_PIG_ID);
  if (!pigNode) {
    console.warn("Domestic pig node not found — skipping breed injection");
    return;
  }

  pigNode.children = PIG_GROUPS.map(group => {
    const groupBreeds = PIG_BREEDS.filter(b => b.group === group);
    return {
      id: `pig-breed-group-${group.toLowerCase()}`,
      name: group,
      rank: "BREED_GROUP",
      lineage: "Pig",
      children: groupBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Pig",
        })),
    };
  });

  console.log(`Injected ${PIG_BREEDS.length} pig breeds in ${PIG_GROUPS.length} groups`);
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
  console.log("Fetching Suidae taxonomy from COL ChecklistBank...");
  const SUIDAE_ID = await findTaxonId("Suidae", "family");
  const records = await fetchAll(SUIDAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, SUIDAE_ID);
  injectDomesticPig(tree);
  injectPigBreeds(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const topLevel = tree.children?.map(c => `${c.commonName ?? c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Top level: ${topLevel}`);

  const outPath = join(import.meta.dirname, "../src/data/suidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
