import { writeFileSync } from "fs";
import { join } from "path";
import { BREEDS, DISCIPLINE_GROUPS } from "../src/data/breeds.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const DOMESTIC_HORSE_SCINAME = "Equus ferus caballus";
const DOMESTIC_HORSE_SYNONYMS = new Set(["Equus ferus caballus", "Equus caballus"]);
export const DOMESTIC_HORSE_ID = "DOMESTIC_HORSE";

const COMMON_NAMES: Record<string, string> = {
  "Equus przewalskii": "Przewalski's Horse",
  "Equus asinus":      "Domestic Donkey",
  "Equus africanus":   "African Wild Ass",
  "Equus hemionus":    "Onager",
  "Equus kiang":       "Kiang",
  "Equus quagga":      "Plains Zebra",
  "Equus zebra":       "Mountain Zebra",
  "Equus grevyi":      "Grévy's Zebra",
};

const SUBSPECIES_COMMON_NAMES: Record<string, string> = {
  // Wild Horse
  "Equus ferus przewalskii":   "Przewalski's Horse",
  "Equus ferus ferus":         "Tarpan",
  // African Wild Ass
  "Equus africanus africanus": "Nubian Wild Ass",
  "Equus africanus somaliensis":"Somali Wild Ass",
  // Onager
  "Equus hemionus hemionus":   "Mongolian Wild Ass",
  "Equus hemionus onager":     "Persian Onager",
  "Equus hemionus khur":       "Indian Wild Ass",
  "Equus hemionus luteus":     "Gobi Khulan",
  // Kiang
  "Equus kiang kiang":         "Western Kiang",
  "Equus kiang holdereri":     "Eastern Kiang",
  "Equus kiang polyodon":      "Southern Kiang",
  // Plains Zebra
  "Equus quagga burchellii":   "Burchell's Zebra",
  "Equus quagga boehmi":       "Grant's Zebra",
  "Equus quagga crawshayi":    "Crawshay's Zebra",
  "Equus quagga chapmani":     "Chapman's Zebra",
  "Equus quagga antiquorum":   "Damara Zebra",
  // Mountain Zebra
  "Equus zebra zebra":         "Cape Mountain Zebra",
  "Equus zebra hartmannae":    "Hartmann's Mountain Zebra",
};

// All Equidae are genus Equus — lineage assigned by species name, not genus
const LINEAGE_BY_SPECIES: Record<string, string> = {
  "Equus przewalskii": "Horse",
  "Equus asinus":      "Ass",
  "Equus africanus":   "Ass",
  "Equus hemionus":    "Ass",
  "Equus kiang":       "Ass",
  "Equus quagga":      "Zebra",
  "Equus zebra":       "Zebra",
  "Equus grevyi":      "Zebra",
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
  hybridParents?: [string, string];
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

function getLineage(sciName: string): string | undefined {
  // Match by full species name (first two words)
  const parts = sciName.split(" ");
  const speciesName = parts.slice(0, 2).join(" ");
  return LINEAGE_BY_SPECIES[speciesName];
}

function buildTree(records: ApiRecord[], rootId: string): TaxonNode {
  const byId = new Map<string, TaxonNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
    if (DOMESTIC_HORSE_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_HORSE_SYNONYMS.has(u.name.scientificName)) continue;
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
    if (DOMESTIC_HORSE_SYNONYMS.has(u.name.scientificName)) continue;
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
  if (!root) throw new Error(`Equidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

function injectDomesticHorse(tree: TaxonNode): void {
  function findNode(node: TaxonNode, predicate: (n: TaxonNode) => boolean): TaxonNode | undefined {
    if (predicate(node)) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, predicate);
      if (found) return found;
    }
  }

  const equusGenus = findNode(tree, n => n.rank === "GENUS" && n.name === "Equus");
  if (!equusGenus) {
    console.warn("Equus genus not found — skipping domestic horse injection");
    return;
  }

  const horseNode: TaxonNode = {
    id: DOMESTIC_HORSE_ID,
    name: DOMESTIC_HORSE_SCINAME,
    rank: "SPECIES",
    commonName: "Domestic Horse",
    lineage: "Horse",
    continents: ["North America", "South America", "Europe", "Asia", "Africa"],
  };

  equusGenus.children = [...(equusGenus.children ?? []), horseNode].sort((a, b) => a.name.localeCompare(b.name));
  console.log("Injected domestic horse node into Equus genus");
}

function injectBreeds(tree: TaxonNode): void {
  function findNode(node: TaxonNode, id: string): TaxonNode | undefined {
    if (node.id === id) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, id);
      if (found) return found;
    }
  }

  const horseNode = findNode(tree, DOMESTIC_HORSE_ID);
  if (!horseNode) {
    console.warn("Domestic horse node not found — skipping breed injection");
    return;
  }

  horseNode.children = DISCIPLINE_GROUPS.map(group => {
    const groupBreeds = BREEDS.filter(b => b.group === group);
    return {
      id: `breed-group-${group.toLowerCase()}`,
      name: group,
      rank: "BREED_GROUP",
      lineage: "Horse",
      children: groupBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Horse",
        })),
    };
  });

  console.log(`Injected ${BREEDS.length} breeds in ${DISCIPLINE_GROUPS.length} discipline groups under domestic horse`);
}

function injectHybrids(tree: TaxonNode): void {
  // Find IDs for Equus africanus and Equus quagga
  function findNode(node: TaxonNode, predicate: (n: TaxonNode) => boolean): TaxonNode | undefined {
    if (predicate(node)) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, predicate);
      if (found) return found;
    }
  }

  const asinus  = findNode(tree, n => n.name === "Equus asinus");
  const quagga  = findNode(tree, n => n.name === "Equus quagga");

  if (!asinus || !quagga) {
    console.warn(`Missing hybrid parents: asinus=${asinus?.id}, quagga=${quagga?.id}`);
    return;
  }

  const hybridGroup: TaxonNode = {
    id: "hybrids-group",
    name: "Hybrids",
    rank: "HYBRID_GROUP",
    children: [
      {
        id: "hybrid-mule",
        name: "Mule",
        rank: "HYBRID",
        commonName: "Mule",
        hybridParents: [asinus.id, DOMESTIC_HORSE_ID],
        lineage: "Donkey ♂ × Horse ♀",
      },
      {
        id: "hybrid-hinny",
        name: "Hinny",
        rank: "HYBRID",
        commonName: "Hinny",
        hybridParents: [DOMESTIC_HORSE_ID, asinus.id],
        lineage: "Horse ♂ × Donkey ♀",
      },
      {
        id: "hybrid-zorse",
        name: "Zorse",
        rank: "HYBRID",
        commonName: "Zorse",
        hybridParents: [quagga.id, DOMESTIC_HORSE_ID],
        lineage: "Zebra ♂ × Horse ♀",
      },
      {
        id: "hybrid-zedonk",
        name: "Zedonk",
        rank: "HYBRID",
        commonName: "Zedonk",
        hybridParents: [quagga.id, asinus.id],
        lineage: "Zebra ♂ × Donkey ♀",
      },
    ],
  };

  tree.children = [...(tree.children ?? []), hybridGroup];
  console.log(`Injected hybrid group with 4 hybrids (asinus: ${asinus.id}, quagga: ${quagga.id})`);
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
  console.log("Fetching Equidae taxonomy from COL ChecklistBank...");
  const EQUIDAE_ID = await findFamilyId("Equidae");
  const records = await fetchAll(EQUIDAE_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, EQUIDAE_ID);
  injectDomesticHorse(tree);
  injectBreeds(tree);
  injectHybrids(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const topLevel = tree.children?.map(c => `${c.commonName ?? c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Top level: ${topLevel}`);

  const outPath = join(import.meta.dirname, "../src/data/equidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
