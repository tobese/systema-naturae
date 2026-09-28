import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Anguilla anguilla":    "European Eel",
  "Anguilla rostrata":    "American Eel",
  "Anguilla japonica":    "Japanese Eel",
  "Anguilla australis":   "Short-finned Eel",
  "Anguilla dieffenbachii": "New Zealand Longfin Eel",
  "Anguilla reinhardtii": "Australian Longfin Eel",
  "Anguilla marmorata":   "Giant Mottled Eel",
  "Anguilla bicolor":     "Shortfin Eel",
  "Anguilla bengalensis": "Indian Mottled Eel",
  "Anguilla obscura":     "Pacific Shortfin Eel",
  "Anguilla megastoma":   "Polynesian Longfin Eel",
  "Anguilla mossambica":  "African Longfin Eel",
  "Anguilla nebulosa":    "African Mottled Eel",
  "Anguilla celebesensis": "Celebes Eel",
  "Anguilla interioris":  "Highlands Eel",
  "Anguilla borneensis":  "Borneo Eel",
  "Anguilla luzonensis":  "Luzon Eel",
  "Anguilla malgumora":   "Indonesian Eel",
};

const LINEAGE = "Freshwater eels";

const CONTINENTS: Record<string, string[]> = {
  "Anguilla anguilla":     ["Europe", "Africa"],
  "Anguilla rostrata":     ["North America"],
  "Anguilla japonica":     ["Asia"],
  "Anguilla australis":    ["Australia", "Oceania"],
  "Anguilla dieffenbachii": ["Oceania"],
  "Anguilla reinhardtii":  ["Australia"],
  "Anguilla marmorata":    ["Asia", "Africa", "Oceania"],
  "Anguilla bicolor":      ["Asia", "Africa", "Australia"],
  "Anguilla bengalensis":  ["Asia"],
  "Anguilla obscura":      ["Oceania"],
  "Anguilla megastoma":    ["Oceania"],
  "Anguilla mossambica":   ["Africa"],
  "Anguilla nebulosa":     ["Africa"],
  "Anguilla celebesensis": ["Asia"],
  "Anguilla interioris":   ["Asia"],
  "Anguilla borneensis":   ["Asia"],
  "Anguilla luzonensis":   ["Asia"],
  "Anguilla malgumora":    ["Asia"],
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
    const node: TreeNode = {
      id: r.id,
      name: sciName,
      rank,
      ...(COMMON_NAMES[sciName] && { commonName: COMMON_NAMES[sciName] }),
      ...(CONTINENTS[sciName] && { continents: [...CONTINENTS[sciName]] }),
    };
    // Set lineage for Anguilla (the only genus in Anguillidae)
    const genus = sciName.split(" ")[0];
    if (genus === "Anguilla" || rank === "GENUS") {
      node.lineage = LINEAGE;
    }
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
      node.description = `${genus} ${epithet} is a freshwater eel species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Anguillidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Anguillidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Anguillidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/anguillidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
