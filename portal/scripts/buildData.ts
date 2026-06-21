import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../../");
const portalRoot = resolve(__dirname, "..");

interface TaxonNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  lineage?: string;
  familySlug?: string;
  appSlug?: string;
  className?: string;
  orderName?: string;
  [key: string]: unknown;
  children?: TaxonNode[];
}

function stampFamilySlug(node: TaxonNode, slug: string, cls?: string, ord?: string): TaxonNode {
  return {
    ...node,
    familySlug: slug,
    className: cls,
    orderName: ord,
    children: node.children?.map(c => stampFamilySlug(c, slug, cls, ord)),
  };
}

function graftFamily(portalNode: TaxonNode, familyData: TaxonNode, slug: string, cls?: string, ord?: string): TaxonNode {
  let children: TaxonNode[];

  if (familyData.rank === "TRIBE") {
    // Caprinae: data root is TRIBE (Caprini) — skip wrapper, use its children directly
    children = (familyData.children ?? []).map(c => stampFamilySlug(c, slug, cls, ord));
  } else {
    // All others: use the family data's children
    children = (familyData.children ?? []).map(c => stampFamilySlug(c, slug, cls, ord));
  }

  // Keep the portal node's own id, rank, name, appSlug, speciesCount etc.
  // Stamp the FAMILY node itself with familySlug too
  return { ...portalNode, familySlug: slug, className: cls, orderName: ord, children };
}

function stampClassOrder(node: TaxonNode, cls?: string, ord?: string): TaxonNode {
  return { ...node, className: cls, orderName: ord };
}

function processTree(node: TaxonNode, ctx: { cls?: string; ord?: string } = {}): TaxonNode {
  let next = ctx;
  if (node.rank === "CLASS") next = { cls: node.name.toLowerCase() };
  if (node.rank === "ORDER") next = { ...ctx, ord: node.name.toLowerCase() };

  if (node.rank === "FAMILY" && node.appSlug) {
    const slug = node.appSlug as string;
    const parts = [next.cls, next.ord, slug].filter(Boolean) as string[];
    const dataPath = resolve(root, ...parts, "src/data", `${slug}.json`);
    try {
      const familyData = JSON.parse(readFileSync(dataPath, "utf-8")) as TaxonNode;
      return graftFamily(node, familyData, slug, next.cls, next.ord);
    } catch (e) {
      console.warn(`  Warning: could not load ${dataPath}: ${(e as Error).message}`);
      return stampClassOrder(node, next.cls, next.ord);
    }
  }
  const stamped = stampClassOrder(node, next.cls, next.ord);
  if (node.children) {
    return { ...stamped, children: node.children.map(c => processTree(c, next)) };
  }
  return stamped;
}

const taxonomyPath = resolve(portalRoot, "data/taxonomy.json");
const outputPath = resolve(portalRoot, "data/unified-taxonomy.json");

console.log("Building unified-taxonomy.json…");
const taxonomy = JSON.parse(readFileSync(taxonomyPath, "utf-8")) as TaxonNode;
const unified = processTree(taxonomy);
writeFileSync(outputPath, JSON.stringify(unified, null, 2));

// Count nodes
let nodeCount = 0;
function count(n: TaxonNode) { nodeCount++; n.children?.forEach(count); }
count(unified);

console.log(`Done. ${nodeCount} total nodes → data/unified-taxonomy.json`);
