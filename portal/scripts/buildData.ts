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
  speciesList?: TaxonNode[];
}

function stampFamilySlug(node: TaxonNode, slug: string, cls?: string, ord?: string): TaxonNode {
  // Detect extinct: name starts with † or description mentions "extinct"
  const name = node.name || "";
  const desc = (node.description as string) || "";
  const isExtinct = name.startsWith("†") || /\bextinct\b/i.test(desc) || /\bfossil\b/i.test(desc);

  return {
    ...node,
    familySlug: slug,
    className: cls,
    orderName: ord,
    extinct: isExtinct,
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

function compressTreeNodes(node: TaxonNode): TaxonNode {
  const processedChildren = node.children?.map(compressTreeNodes);

  if (node.rank === "GENUS") {
    const physicalChildren: TaxonNode[] = [];
    const speciesList: TaxonNode[] = [];

    if (processedChildren) {
      for (const child of processedChildren) {
        if (child.rank === "SPECIES") {
          const desc = (child.description as string) || "";
          const isMinimal = !desc || /a (\w+ )?species in the genus/i.test(desc);
          const hasChildren = child.children && child.children.length > 0;

          if (isMinimal && !hasChildren) {
            const leanChild = { ...child };
            delete leanChild.children;
            speciesList.push(leanChild);
          } else {
            physicalChildren.push(child);
          }
        } else {
          physicalChildren.push(child);
        }
      }
    }

    const updatedNode = { ...node };
    if (physicalChildren.length > 0) {
      updatedNode.children = physicalChildren;
    } else {
      delete updatedNode.children;
    }

    if (speciesList.length > 0) {
      updatedNode.speciesList = speciesList;
    }

    return updatedNode;
  }

  const updatedNode = { ...node };
  if (processedChildren) {
    updatedNode.children = processedChildren;
  }
  return updatedNode;
}

const taxonomyPath = resolve(portalRoot, "data/taxonomy.json");
const outputPath = resolve(portalRoot, "data/unified-taxonomy.json");

console.log("Building unified-taxonomy.json…");
const taxonomy = JSON.parse(readFileSync(taxonomyPath, "utf-8")) as TaxonNode;
const uncompressed = processTree(taxonomy);
const unified = compressTreeNodes(uncompressed);

// Count nodes and stamp rankCounts on root
let physicalCount = 0;
let flatSpeciesCount = 0;
const rankCounts: Record<string, number> = {};
function count(n: TaxonNode) {
  physicalCount++;
  rankCounts[n.rank] = (rankCounts[n.rank] || 0) + 1;
  if (n.speciesList) {
    flatSpeciesCount += n.speciesList.length;
    for (const sp of n.speciesList) {
      rankCounts[sp.rank] = (rankCounts[sp.rank] || 0) + 1;
    }
  }
  n.children?.forEach(count);
}
count(unified);
unified.rankCounts = rankCounts;

writeFileSync(outputPath, JSON.stringify(unified, null, 2));

console.log(`Done. ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species in speciesList (${physicalCount + flatSpeciesCount} total nodes represented) → data/unified-taxonomy.json`);
