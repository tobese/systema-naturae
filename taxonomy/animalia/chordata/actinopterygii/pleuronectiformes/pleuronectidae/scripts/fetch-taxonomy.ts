import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Pleuronectes platessa":        "European Plaice",
  "Platichthys flesus":           "European Flounder",
  "Platichthys stellatus":        "Starry Flounder",
  "Limanda limanda":              "Common Dab",
  "Microstomus kitt":             "Lemon Sole",
  "Glyptocephalus cynoglossus":   "Witch",
  "Hippoglossoides platessoides": "Long Rough Dab",
  "Hippoglossus hippoglossus":    "Atlantic Halibut",
  "Hippoglossus stenolepis":      "Pacific Halibut",
  "Reinhardtius hippoglossoides": "Greenland Halibut",
  "Pseudopleuronectes americanus": "Winter Flounder",
  "Pseudopleuronectes yokohamae": "Marbled Flounder",
  "Verasper variegatus":          "Spotted Halibut",
  "Atheresthes stomias":          "Arrowtooth Flounder",
  "Eopsetta jordani":             "Petrale Sole",
  "Kareius bicoloratus":          "Stone Flounder",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Pleuronectes:       "Plaice & flounders",
  Platichthys:        "Plaice & flounders",
  Pseudopleuronectes: "Plaice & flounders",
  Verasper:           "Plaice & flounders",
  Kareius:            "Plaice & flounders",
  Limanda:            "Dabs & witches",
  Microstomus:        "Dabs & witches",
  Glyptocephalus:     "Dabs & witches",
  Tanakius:           "Dabs & witches",
  Dexistes:           "Dabs & witches",
  Hippoglossoides:    "Long rough dabs",
  Hippoglossus:       "Halibut",
  Reinhardtius:       "Halibut",
  Atheresthes:        "Halibut",
  Eopsetta:           "Soles & flounders",
  Lyopsetta:          "Soles & flounders",
  Embassichthys:      "Soles & flounders",
  Parophrys:          "Soles & flounders",
  Isopsetta:          "Soles & flounders",
  Psettichthys:       "Soles & flounders",
};

const CONTINENTS: Record<string, string[]> = {
  "Pleuronectes platessa":        ["Europe"],
  "Platichthys flesus":           ["Europe", "Africa"],
  "Platichthys stellatus":        ["North America", "Asia"],
  "Limanda limanda":              ["Europe"],
  "Microstomus kitt":             ["Europe"],
  "Glyptocephalus cynoglossus":   ["Europe", "North America"],
  "Hippoglossoides platessoides": ["Europe", "North America"],
  "Hippoglossus hippoglossus":    ["Europe", "North America"],
  "Hippoglossus stenolepis":      ["North America", "Asia"],
  "Reinhardtius hippoglossoides": ["Europe", "North America", "Asia"],
  "Pseudopleuronectes americanus": ["North America"],
  "Pseudopleuronectes yokohamae": ["Asia"],
  "Verasper variegatus":          ["Asia"],
  "Atheresthes stomias":          ["North America"],
  "Eopsetta jordani":             ["North America"],
  "Kareius bicoloratus":          ["Asia"],
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

interface TreeNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  lineage?: string;
  subspeciesCount?: number;
  continents?: string[];
  description?: string;
  children?: TreeNode[];
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

function buildTree(records: ApiRecord[], rootId: string): TreeNode {
  const byId = new Map<string, TreeNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
    const sciName = u.name.scientificName;
    const rank = u.name.rank.toUpperCase();
    const genus = sciName.split(" ")[0];
    const node: TreeNode = {
      id: r.id,
      name: sciName,
      rank,
      ...(COMMON_NAMES[sciName] && { commonName: COMMON_NAMES[sciName] }),
      ...(LINEAGE_BY_GENUS[genus] && { lineage: LINEAGE_BY_GENUS[genus] }),
      ...(CONTINENTS[sciName] && { continents: [...CONTINENTS[sciName]] }),
    };
    byId.set(r.id, node);
  }

  const subspeciesCounts = new Map<string, number>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (u.name.rank.toUpperCase() === "SUBSPECIES" && u.parentId) {
      subspeciesCounts.set(u.parentId, (subspeciesCounts.get(u.parentId) ?? 0) + 1);
    }
  }
  for (const [id, count] of subspeciesCounts) {
    const node = byId.get(id);
    if (node) node.subspeciesCount = count;
  }

  const childrenMap = new Map<string, TreeNode[]>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (!u.parentId) continue;
    const node = byId.get(r.id);
    if (!node) continue;
    const siblings = childrenMap.get(u.parentId) ?? [];
    siblings.push(node);
    childrenMap.set(u.parentId, siblings);
  }

  function attach(node: TreeNode): TreeNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(attach).sort((a, b) => a.name.localeCompare(b.name));
    }
    if (node.rank === "SPECIES" && !node.description) {
      const parts = node.name.split(" ");
      const genus = parts[0];
      const epithet = parts.slice(1).join(" ");
      const lineage = node.lineage ?? "flatfish";
      node.description = `${genus} ${epithet} is a ${lineage} species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Pleuronectidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Pleuronectidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Pleuronectidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/pleuronectidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
