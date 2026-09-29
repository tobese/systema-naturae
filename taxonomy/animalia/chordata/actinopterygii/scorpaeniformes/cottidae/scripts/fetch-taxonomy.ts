import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Cottus gobio":             "European Bullhead",
  "Cottus poecilopus":        "Alpine Bullhead",
  "Cottus cognatus":          "Slimy Sculpin",
  "Cottus bairdii":           "Mottled Sculpin",
  "Cottus perplexus":         "Reticulate Sculpin",
  "Cottus aleuticus":         "Coastrange Sculpin",
  "Cottus asper":             "Prickly Sculpin",
  "Cottus rhotheus":          "Torrent Sculpin",
  "Cottus beldingii":         "Paiute Sculpin",
  "Cottus carolinae":         "Banded Sculpin",
  "Myoxocephalus scorpius":   "Shorthorn Sculpin",
  "Myoxocephalus octodecemspinosus": "Longhorn Sculpin",
  "Myoxocephalus quadricornis": "Fourhorn Sculpin",
  "Myoxocephalus aenaeus":    "Grubby Sculpin",
  "Myoxocephalus polyacanthocephalus": "Great Sculpin",
  "Gymnocanthus tricuspis":   "Arctic Staghorn Sculpin",
  "Icelus bicornis":          "Twohorn Sculpin",
  "Triglops pingelii":        "Ribbed Sculpin",
  "Triglops murrayi":         "Moustache Sculpin",
  "Enophrys diceraus":        "Antlered Sculpin",
  "Enophrys lucasi":          "Leister Sculpin",
  "Hemilepidotus hemilepidotus": "Red Irish Lord",
  "Hemilepidotus jordani":    "Yellow Irish Lord",
  "Taurulus bubalis":         "Longspined Bullhead",
  "Leptocottus armatus":      "Pacific Staghorn Sculpin",
  "Oligocottus maculosus":    "Tidepool Sculpin",
  "Blepsias cirrhosus":       "Silverspotted Sculpin",
  "Nautichthys oculofasciatus": "Sailfin Sculpin",
  "Scorpaenichthys marmoratus": "Cabezon",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Cottus:          "Freshwater sculpins",
  Myoxocephalus:   "Marine sculpins",
  Gymnocanthus:    "Arctic sculpins",
  Icelus:          "Arctic sculpins",
  Triglops:        "Arctic sculpins",
  Enophrys:        "Marine sculpins",
  Hemilepidotus:   "Marine sculpins",
  Taurulus:        "Marine sculpins",
  Leptocottus:     "Marine sculpins",
  Oligocottus:     "Tidepool sculpins",
  Clinocottus:     "Tidepool sculpins",
  Orthonopias:     "Tidepool sculpins",
  Blennicottus:    "Tidepool sculpins",
  Artedius:        "Tidepool sculpins",
  Oxycottus:       "Tidepool sculpins",
  Blepsias:        "Marine sculpins",
  Nautichthys:     "Marine sculpins",
  Scorpaenichthys: "Marine sculpins",
  Jordania:        "Marine sculpins",
};

const CONTINENTS: Record<string, string[]> = {
  "Cottus gobio":             ["Europe"],
  "Cottus poecilopus":        ["Europe"],
  "Cottus cognatus":          ["North America", "Europe", "Asia"],
  "Cottus bairdii":           ["North America"],
  "Cottus perplexus":         ["North America"],
  "Cottus aleuticus":         ["North America"],
  "Cottus asper":             ["North America"],
  "Cottus rhotheus":          ["North America"],
  "Cottus beldingii":         ["North America"],
  "Cottus carolinae":         ["North America"],
  "Myoxocephalus scorpius":   ["Europe", "North America"],
  "Myoxocephalus octodecemspinosus": ["North America"],
  "Myoxocephalus quadricornis": ["Europe", "North America", "Asia"],
  "Myoxocephalus aenaeus":    ["North America"],
  "Myoxocephalus polyacanthocephalus": ["North America", "Asia"],
  "Gymnocanthus tricuspis":   ["Europe", "North America", "Asia"],
  "Icelus bicornis":          ["Europe", "North America"],
  "Triglops pingelii":        ["Europe", "North America"],
  "Triglops murrayi":         ["Europe", "North America"],
  "Enophrys diceraus":        ["North America", "Asia"],
  "Enophrys lucasi":          ["North America"],
  "Hemilepidotus hemilepidotus": ["North America"],
  "Hemilepidotus jordani":    ["North America"],
  "Taurulus bubalis":         ["Europe"],
  "Leptocottus armatus":      ["North America"],
  "Oligocottus maculosus":    ["North America"],
  "Blepsias cirrhosus":       ["North America"],
  "Nautichthys oculofasciatus": ["North America"],
  "Scorpaenichthys marmoratus": ["North America"],
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
      const lineage = node.lineage ?? "sculpin";
      node.description = `${genus} ${epithet} is a ${lineage} species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Cottidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Cottidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Cottidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/cottidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
