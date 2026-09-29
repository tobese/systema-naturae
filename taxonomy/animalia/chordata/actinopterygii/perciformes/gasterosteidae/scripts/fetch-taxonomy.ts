import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Gasterosteus aculeatus":  "Three-spined Stickleback",
  "Gasterosteus nipponicus": "Japanese Stickleback",
  "Gasterosteus microcephalus": "Small-headed Stickleback",
  "Gasterosteus wheatlandi": "Black-spotted Stickleback",
  "Pungitius pungitius":     "Ninespine Stickleback",
  "Pungitius laevis":        "Smoothtail Ninespine Stickleback",
  "Pungitius platygaster":   "Southern Ninespine Stickleback",
  "Pungitius hellenicus":    "Greek Ninespine Stickleback",
  "Spinachia spinachia":     "Fifteen-spined Stickleback",
  "Apeltes quadracus":       "Fourspine Stickleback",
  "Culaea inconstans":       "Brook Stickleback",
};

const GENERA_LINEAGE: Record<string, string> = {
  Gasterosteus: "Typical sticklebacks",
  Pungitius:    "Ninespine sticklebacks",
  Spinachia:    "Sea sticklebacks",
  Apeltes:      "Fourspine sticklebacks",
  Culaea:       "Brook sticklebacks",
};

const CONTINENTS: Record<string, string[]> = {
  "Gasterosteus aculeatus":  ["Europe", "Asia", "North America"],
  "Gasterosteus nipponicus": ["Asia"],
  "Gasterosteus microcephalus": ["North America"],
  "Gasterosteus wheatlandi": ["North America"],
  "Pungitius pungitius":     ["Europe", "Asia", "North America"],
  "Pungitius laevis":        ["Europe"],
  "Pungitius platygaster":   ["Europe", "Asia"],
  "Pungitius hellenicus":    ["Europe"],
  "Spinachia spinachia":     ["Europe"],
  "Apeltes quadracus":       ["North America"],
  "Culaea inconstans":       ["North America"],
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
      ...(GENERA_LINEAGE[genus] && { lineage: GENERA_LINEAGE[genus] }),
      ...(CONTINENTS[sciName] && { continents: CONTINENTS[sciName] }),
    };
    for (const spName of Object.keys(CONTINENTS)) {
      if (sciName === spName) {
        node.continents = [...CONTINENTS[spName]];
        break;
      }
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

  function attach(node: TreeNode, depth: number): TreeNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(c => attach(c, depth + 1)).sort((a, b) => a.name.localeCompare(b.name));
    }
    // Generate description for species using lineage
    if (node.rank === "SPECIES" && !node.description) {
      const lineage = node.lineage ?? "stickleback";
      const nameParts = node.name.split(" ");
      const genus = nameParts[0];
      const epithet = nameParts.slice(1).join(" ");
      node.description = `${genus} ${epithet} is a ${lineage} species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Gasterosteidae root not found: ${rootId}`);
  return attach(root, 0);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Gasterosteidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Gasterosteidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/gasterosteidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
