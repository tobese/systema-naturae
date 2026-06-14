import { writeFileSync } from "fs";
import { join } from "path";
import { BREEDS, REGIONS } from "../src/data/breeds.js";
import { HYBRIDS } from "../src/data/hybrids.js";
import { SPECIES_RANGES } from "../src/data/ranges.js";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";
const FELIDAE_ID = "623RM";

const COMMON_NAMES: Record<string, string> = {
  "Panthera leo": "Lion",
  "Panthera tigris": "Tiger",
  "Panthera pardus": "Leopard",
  "Panthera onca": "Jaguar",
  "Panthera uncia": "Snow leopard",
  "Neofelis nebulosa": "Clouded leopard",
  "Neofelis diardi": "Sunda clouded leopard",
  "Acinonyx jubatus": "Cheetah",
  "Puma concolor": "Cougar",
  "Lynx lynx": "Eurasian lynx",
  "Lynx pardinus": "Iberian lynx",
  "Lynx canadensis": "Canada lynx",
  "Lynx rufus": "Bobcat",
  "Leopardus pardalis": "Ocelot",
  "Leopardus wiedii": "Margay",
  "Leopardus tigrinus": "Oncilla",
  "Leopardus guttulus": "Southern tigrina",
  "Leopardus geoffroyi": "Geoffroy's cat",
  "Leopardus colocola": "Pampas cat",
  "Leopardus guigna": "Kodkod",
  "Leopardus jacobita": "Andean mountain cat",
  "Caracal caracal": "Caracal",
  "Caracal aurata": "African golden cat",
  "Leptailurus serval": "Serval",
  "Felis catus": "Domestic cat",
  "Felis silvestris": "European wildcat",
  "Felis lybica": "African wildcat",
  "Felis chaus": "Jungle cat",
  "Felis margarita": "Sand cat",
  "Felis nigripes": "Black-footed cat",
  "Felis bieti": "Chinese mountain cat",
  "Prionailurus bengalensis": "Leopard cat",
  "Prionailurus viverrinus": "Fishing cat",
  "Prionailurus planiceps": "Flat-headed cat",
  "Prionailurus rubiginosus": "Rusty-spotted cat",
  "Prionailurus javanensis": "Sunda leopard cat",
  "Otocolobus manul": "Pallas's cat",
  "Catopuma temminckii": "Asian golden cat",
  "Catopuma badia": "Bay cat",
  "Pardofelis marmorata": "Marbled cat",
  "Herpailurus yagouaroundi": "Jaguarundi",
};

const SUBSPECIES_COMMON_NAMES: Record<string, string> = {
  // Lions
  "Panthera leo leo":               "Northern Lion",
  "Panthera leo melanochaita":      "Southern Lion",
  // Tigers
  "Panthera tigris altaica":        "Amur Tiger",
  "Panthera tigris tigris":         "Bengal Tiger",
  "Panthera tigris sumatrae":       "Sumatran Tiger",
  "Panthera tigris corbetti":       "Indochinese Tiger",
  "Panthera tigris jacksoni":       "Malayan Tiger",
  "Panthera tigris sondaica":       "Javan Tiger",
  // Leopards
  "Panthera pardus pardus":         "African Leopard",
  "Panthera pardus delacouri":      "Indochinese Leopard",
  "Panthera pardus orientalis":     "Amur Leopard",
  "Panthera pardus fusca":          "Indian Leopard",
  "Panthera pardus kotiya":         "Sri Lankan Leopard",
  "Panthera pardus melas":          "Javan Leopard",
  "Panthera pardus nimr":           "Arabian Leopard",
  "Panthera pardus saxicolor":      "Persian Leopard",
  "Panthera pardus japonensis":     "North Chinese Leopard",
  "Panthera pardus tulliana":       "Anatolian Leopard",
  // Jaguars
  "Panthera onca onca":             "Amazon Jaguar",
  "Panthera onca palustris":        "Pantanal Jaguar",
  // Cheetahs
  "Acinonyx jubatus jubatus":       "Southern Cheetah",
  "Acinonyx jubatus venaticus":     "Asiatic Cheetah",
  "Acinonyx jubatus raineyi":       "East African Cheetah",
  "Acinonyx jubatus soemmeringii":  "Northeast African Cheetah",
  "Acinonyx jubatus hecki":         "Northwest African Cheetah",
  // Eurasian lynx
  "Lynx lynx lynx":                 "Eurasian Lynx (nominate)",
  "Lynx lynx isabellinus":          "Central Asian Lynx",
  "Lynx lynx dinniki":              "Caucasian Lynx",
  "Lynx lynx carpathicus":          "Carpathian Lynx",
  "Lynx lynx wrangeli":             "Siberian Lynx",
  // Serval
  "Leptailurus serval serval":      "Southern Serval",
  "Leptailurus serval lipostictus": "Northern Serval",
  // Puma
  "Puma concolor concolor":         "South American Cougar",
  "Puma concolor couguar":          "North American Cougar",
  // Ocelot
  "Leopardus pardalis pardalis":    "Amazon Ocelot",
  "Leopardus pardalis mitis":       "Southern Ocelot",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Catopuma: "Bay cat",
  Pardofelis: "Bay cat",
  Caracal: "Caracal",
  Leptailurus: "Caracal",
  Leopardus: "Ocelot",
  Lynx: "Lynx",
  Acinonyx: "Puma",
  Herpailurus: "Puma",
  Puma: "Puma",
  Otocolobus: "Leopard cat",
  Prionailurus: "Leopard cat",
  Felis: "Domestic cat",
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
  wildParentId?: string;
  wildParentName?: string;
  coatType?: string;
  continents?: string[];
  accepted?: boolean;
  children?: TaxonNode[];
}

async function fetchPage(offset: number, limit = 500): Promise<{ records: ApiRecord[]; total: number }> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?TAXON_ID=${FELIDAE_ID}&limit=${limit}&offset=${offset}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[]; total: number };
  return { records: json.result, total: json.total };
}

async function fetchAll(): Promise<ApiRecord[]> {
  const records: ApiRecord[] = [];
  const { records: first, total } = await fetchPage(0);
  records.push(...first);
  console.log(`Total: ${total} taxa, batch 1: ${first.length}`);
  for (let offset = first.length; offset < total; offset += 500) {
    const { records: page } = await fetchPage(offset);
    records.push(...page);
    console.log(`  fetched ${records.length}/${total}`);
  }
  return records;
}

function buildTree(records: ApiRecord[]): TaxonNode {
  const byId = new Map<string, TaxonNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
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

  // Count subspecies per species parent
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

  const childrenMap = new Map<string, TaxonNode[]>();
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

  // Second pass: inject non-accepted subspecies (synonyms) under their parent species,
  // identified by extracting the binomial prefix from the trinomial name.
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
    if (acceptedSubspeciesNames.has(sciName)) continue; // already included as accepted
    const parts = sciName.split(" ");
    if (parts.length < 3) continue;
    const speciesName = `${parts[0]} ${parts[1]}`;
    const parentSpecies = speciesByName.get(speciesName);
    if (!parentSpecies) continue;
    // Avoid duplicates
    const siblings = childrenMap.get(parentSpecies.id) ?? [];
    if (siblings.some(c => c.name === sciName)) continue;
    // Only include non-accepted subspecies that have a well-known common name
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
  console.log(`Added ${synonymCount} non-accepted subspecies (synonyms)`);

  function attach(node: TaxonNode): TaxonNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(attach).sort((a, b) => a.name.localeCompare(b.name));
    }
    return node;
  }

  const root = byId.get(FELIDAE_ID);
  if (!root) throw new Error("Felidae root not found in results");
  return attach(root);
}

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

const FELIS_CATUS_ID = "3DXV3";

function injectBreeds(tree: TaxonNode): void {
  function findNode(node: TaxonNode, id: string): TaxonNode | undefined {
    if (node.id === id) return node;
    for (const child of node.children ?? []) {
      const found = findNode(child, id);
      if (found) return found;
    }
  }

  const felisCatus = findNode(tree, FELIS_CATUS_ID);
  if (!felisCatus) {
    console.warn("Felis catus node not found — skipping breed injection");
    return;
  }

  felisCatus.children = REGIONS.map(region => {
    const regionBreeds = BREEDS.filter(b => b.region === region);
    return {
      id: `breed-group-${region.toLowerCase().replace(/[^a-z]/g, "-")}`,
      name: region,
      rank: "BREED_GROUP",
      lineage: "Domestic cat",
      children: regionBreeds
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(b => ({
          id: b.id,
          name: b.name,
          rank: "BREED",
          origin: b.origin,
          lineage: "Domestic cat",
          coatType: b.coatType,
          ...(b.wildParentId && { wildParentId: b.wildParentId, wildParentName: b.wildParentName }),
        })),
    };
  });

  console.log(`Injected ${BREEDS.length} breeds in ${REGIONS.length} regional groups under Felis catus`);
}

function injectHybrids(tree: TaxonNode): void {
  const hybridGroup: TaxonNode = {
    id: "hybrids-group",
    name: "Hybrids",
    rank: "HYBRID_GROUP",
    children: HYBRIDS.map(h => ({
      id: h.id,
      name: h.name,
      rank: "HYBRID",
      commonName: h.name,
      hybridParents: h.hybridParents,
      // Store description in lineage field for convenience (no separate field in TaxonNode)
      lineage: h.description,
    })),
  };
  tree.children = [...(tree.children ?? []), hybridGroup];
  console.log(`Injected ${HYBRIDS.length} hybrids in Hybrids group`);
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
  console.log("Fetching Felidae taxonomy from COL ChecklistBank...");
  const records = await fetchAll();
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records);
  injectBreeds(tree);
  injectHybrids(tree);
  injectRanges(tree);

  const leaves = countLeaves(tree);
  console.log(`Total leaves (species + breeds): ${leaves}`);
  console.log(`Subfamilies: ${tree.children?.map(c => `${c.name} (${countLeaves(c)} spp)`).join(", ")}`);

  const outPath = join(import.meta.dirname, "../src/data/felidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
