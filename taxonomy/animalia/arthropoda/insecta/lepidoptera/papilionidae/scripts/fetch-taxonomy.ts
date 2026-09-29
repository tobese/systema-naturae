import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Papilio machaon":           "Old World Swallowtail",
  "Papilio polyxenes":         "Black Swallowtail",
  "Papilio glaucus":           "Eastern Tiger Swallowtail",
  "Papilio rutulus":           "Western Tiger Swallowtail",
  "Papilio canadensis":        "Canadian Tiger Swallowtail",
  "Papilio troilus":           "Spicebush Swallowtail",
  "Papilio cresphontes":       "Giant Swallowtail",
  "Papilio multicaudata":      "Two-tailed Swallowtail",
  "Papilio indra":             "Indra Swallowtail",
  "Papilio demoleus":          "Lime Swallowtail",
  "Papilio helenus":           "Red Helen",
  "Papilio memnon":            "Great Mormon",
  "Papilio polytes":           "Common Mormon",
  "Papilio xuthus":            "Asian Swallowtail",
  "Papilio hospiton":          "Corsican Swallowtail",
  "Papilio alexanor":          "Alexanor Swallowtail",
  "Parnassius apollo":         "Apollo Butterfly",
  "Parnassius mnemosyne":      "Clouded Apollo",
  "Parnassius phoebus":        "Small Apollo",
  "Parnassius smintheus":      "Rocky Mountain Apollo",
  "Iphiclides podalirius":     "Scarce Swallowtail",
  "Iphiclides feisthamelii":   "Iberian Scarce Swallowtail",
  "Zerynthia polyxena":        "Southern Festoon",
  "Zerynthia rumina":          "Spanish Festoon",
  "Graphium sarpedon":         "Common Bluebottle",
  "Graphium agamemnon":        "Tailed Jay",
  "Graphium doson":            "Common Jay",
  "Graphium eurypylus":        "Great Jay",
  "Graphium macleayanum":      "Macleay's Swallowtail",
  "Ornithoptera alexandrae":   "Queen Alexandra's Birdwing",
  "Ornithoptera priamus":      "Common Green Birdwing",
  "Ornithoptera croesus":      "Wallace's Golden Birdwing",
  "Troides helena":            "Common Birdwing",
  "Troides aeacus":            "Golden Birdwing",
  "Troides magellanus":        "Magellan Birdwing",
  "Parides aeneas":            "Aeneas Cattleheart",
  "Parides sesostris":         "Emerald-patched Cattleheart",
  "Parides photinus":          "Pink-spotted Cattleheart",
  "Battus philenor":           "Pipevine Swallowtail",
  "Battus polydamas":          "Polydamas Swallowtail",
  "Eurytides marcellus":       "Zebra Swallowtail",
  "Eurytides thyastes":        "Thyastes Swallowtail",
  "Mimoides thymbraeus":       "White-crescent Swallowtail",
  "Protesilaus protesilaus":   "Protesilaus Swallowtail",
  "Lamproptera curius":        "White Dragontail",
  "Lamproptera meges":         "Green Dragontail",
  "Teinopalpus imperialis":    "Kaiser-i-Hind",
  "Bhutanitis ludlowi":        "Ludlow's Bhutan Swallowtail",
  "Bhutanitis thaidina":       "Chinese Bhutan Swallowtail",
  "Luehdorfia japonica":       "Japanese Luehdorfia",
  "Luehdorfia chinensis":      "Chinese Luehdorfia",
  "Sericinus montela":         "Amur Swallowtail",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Papilio:      "Swallowtails",
  Parnassius:   "Apollos",
  Iphiclides:   "Scarce swallowtails",
  Zerynthia:    "Festoons",
  Graphium:     "Swordtails",
  Ornithoptera: "Birdwings",
  Troides:      "Birdwings",
  Parides:      "Birdwings & cattlehearts",
  Battus:       "Pipevine swallowtails",
  Eurytides:    "Kite swallowtails",
  Mimoides:     "Mimic swallowtails",
  Protesilaus:  "Kite swallowtails",
  Lamproptera:  "Dragontails",
  Teinopalpus:  "Kaiser-i-Hind",
  Bhutanitis:   "Bhutan swallowtails",
  Luehdorfia:   "Luehdorfia",
  Sericinus:    "Sericinus",
  Meandrusa:    "Hook-tip swallowtails",
  Chilasa:      "Mimic swallowtails",
};

const CONTINENTS: Record<string, string[]> = {
  "Papilio machaon":         ["Europe", "Asia", "North America"],
  "Papilio polyxenes":       ["North America"],
  "Papilio glaucus":         ["North America"],
  "Papilio rutulus":         ["North America"],
  "Papilio canadensis":      ["North America"],
  "Papilio troilus":         ["North America"],
  "Papilio cresphontes":     ["North America"],
  "Papilio multicaudata":    ["North America"],
  "Papilio indra":           ["North America"],
  "Papilio demoleus":        ["Asia", "Australia"],
  "Papilio helenus":         ["Asia"],
  "Papilio memnon":          ["Asia"],
  "Papilio polytes":         ["Asia"],
  "Papilio xuthus":          ["Asia"],
  "Papilio hospiton":        ["Europe"],
  "Papilio alexanor":        ["Europe"],
  "Parnassius apollo":       ["Europe", "Asia"],
  "Parnassius mnemosyne":    ["Europe", "Asia"],
  "Parnassius phoebus":      ["Europe", "North America"],
  "Parnassius smintheus":    ["North America"],
  "Iphiclides podalirius":   ["Europe", "Asia"],
  "Iphiclides feisthamelii": ["Europe"],
  "Zerynthia polyxena":      ["Europe"],
  "Zerynthia rumina":        ["Europe"],
  "Graphium sarpedon":       ["Asia", "Australia"],
  "Graphium agamemnon":      ["Asia", "Australia", "Oceania"],
  "Graphium doson":          ["Asia"],
  "Graphium eurypylus":      ["Asia", "Australia", "Oceania"],
  "Graphium macleayanum":    ["Australia"],
  "Ornithoptera alexandrae": ["Oceania"],
  "Ornithoptera priamus":    ["Asia", "Australia", "Oceania"],
  "Ornithoptera croesus":    ["Asia"],
  "Troides helena":          ["Asia"],
  "Troides aeacus":          ["Asia"],
  "Troides magellanus":      ["Asia"],
  "Parides aeneas":          ["South America"],
  "Parides sesostris":       ["South America"],
  "Parides photinus":        ["South America"],
  "Battus philenor":         ["North America"],
  "Battus polydamas":        ["North America", "South America"],
  "Eurytides marcellus":     ["North America"],
  "Eurytides thyastes":      ["South America"],
  "Mimoides thymbraeus":     ["North America"],
  "Protesilaus protesilaus": ["South America"],
  "Lamproptera curius":      ["Asia"],
  "Lamproptera meges":       ["Asia"],
  "Teinopalpus imperialis":  ["Asia"],
  "Bhutanitis ludlowi":      ["Asia"],
  "Bhutanitis thaidina":     ["Asia"],
  "Luehdorfia japonica":     ["Asia"],
  "Luehdorfia chinensis":    ["Asia"],
  "Sericinus montela":       ["Asia"],
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
      const lineage = node.lineage ?? "swallowtail";
      node.description = `${genus} ${epithet} is a ${lineage} butterfly species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Papilionidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Papilionidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Papilionidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/papilionidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
