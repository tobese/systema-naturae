import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
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
  description?: string;
  children?: TaxonNode[];
  speciesList?: TaxonNode[];
  speciesCount?: number;
  rankCounts?: Record<string, number>;
  extinct?: boolean;
  _familyCount?: number;
  _speciesCount?: number;
  _dataFile?: string;
  [key: string]: unknown;
}

function stampFamilySlug(node: TaxonNode, slug: string, cls?: string, ord?: string): TaxonNode {
  const name = node.name || "";
  const desc = node.description || "";
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
    children = (familyData.children ?? []).map(c => stampFamilySlug(c, slug, cls, ord));
  } else {
    children = (familyData.children ?? []).map(c => stampFamilySlug(c, slug, cls, ord));
  }

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
const ordersDir = resolve(portalRoot, "data/orders");
const skeletonPath = resolve(portalRoot, "data/unified-taxonomy-skeleton.json");
const manifestPath = resolve(portalRoot, "data/order-manifest.json");

console.log("Building unified-taxonomy.json…");
const taxonomy = JSON.parse(readFileSync(taxonomyPath, "utf-8")) as TaxonNode;
const uncompressed = processTree(taxonomy);
const unified = compressTreeNodes(uncompressed);

// ── Count nodes and stamp rankCounts on root ──
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

// ── Still produce the monolithic unified-tree for backward compat ──
writeFileSync(outputPath, JSON.stringify(unified, null, 2));
console.log(`  Unified tree: ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species`);

// ── Extract per-order subtrees ──
if (!existsSync(ordersDir)) mkdirSync(ordersDir, { recursive: true });

interface OrderEntry {
  orderId: string;
  classSlug: string;
  orderSlug: string;
  familyCount: number;
  speciesCount: number;
  familySlugs: string[];
}

const orderMap = new Map<string, OrderEntry>();
const familyToOrder: Record<string, string> = {};

function collectOrders(node: TaxonNode, cls?: string): void {
  if (node.rank === "ORDER") {
    const orderSlug = node.name?.toLowerCase() || "";
    const classSlug = cls?.toLowerCase() || "";
    const familySlugs: string[] = [];

    let speciesCount = 0;
    function walkCount(n: TaxonNode) {
      if (n.rank === "SPECIES") speciesCount++;
      if (n.speciesList) speciesCount += n.speciesList.length;
      for (const c of n.children ?? []) {
        if (c.rank === "FAMILY" && c.familySlug) familySlugs.push(c.familySlug);
        walkCount(c);
      }
    }
    walkCount(node);

    orderMap.set(node.id, {
      orderId: node.id,
      classSlug,
      orderSlug,
      familyCount: familySlugs.length,
      speciesCount,
      familySlugs,
    });

    for (const slug of familySlugs) {
      familyToOrder[slug] = node.id;
    }

    // Write the order data file
    const orderFilePath = resolve(ordersDir, `${node.id}.json`);
    writeFileSync(orderFilePath, JSON.stringify(node, null, 2));
    console.log(`  Order ${node.id}: ${familySlugs.length} families, ${speciesCount} species → ${orderFilePath}`);
    return;
  }

  const nextCls = node.rank === "CLASS" ? (node.name?.toLowerCase() || "") : (cls || "");
  for (const c of node.children ?? []) collectOrders(c, nextCls);
}

{
  const orderCountBefore = orderMap.size;
  collectOrders(unified);
  console.log(`  Extracted ${orderMap.size - orderCountBefore} order data files`);
}

// ── Build skeleton (KINGDOM → PHYLUM → CLASS → ORDER, no family children) ──
function buildSkeleton(node: TaxonNode): TaxonNode {
  if (node.rank === "ORDER") {
    const entry = orderMap.get(node.id);
    const result: TaxonNode = {
      id: node.id,
      name: node.name,
      rank: node.rank,
      commonName: node.commonName,
      description: node.description,
      className: node.className,
      orderName: node.orderName,
      _familyCount: entry?.familyCount ?? 0,
      _speciesCount: entry?.speciesCount ?? 0,
      _dataFile: `data/orders/${node.id}.json`,
    };
    return result;
  }

  const result: TaxonNode = { ...node } as any;
  delete result.children;
  delete result.speciesList;

  if (node.children && node.children.length > 0) {
    const pruned = node.children.map(c => buildSkeleton(c)).filter(Boolean);
    if (pruned.length > 0) result.children = pruned;
  }

  // Recompute family count for higher ranks
  if (node.rank === "KINGDOM" || node.rank === "PHYLUM" || node.rank === "CLASS") {
    let fc = 0;
    function walkFc(n: TaxonNode) {
      for (const c of n.children ?? []) {
        if (c.rank === "FAMILY") fc++;
        else walkFc(c);
      }
    }
    walkFc(node);
    result._familyCount = fc;
  }

  return result;
}

const skeleton = buildSkeleton(unified);
skeleton.rankCounts = rankCounts;

writeFileSync(skeletonPath, JSON.stringify(skeleton, null, 2));
console.log(`  Skeleton: → ${skeletonPath}`);

// ── Build manifest ──
interface ManifestEntry {
  orderId: string;
  classSlug: string;
  orderSlug: string;
  file: string;
  familyCount: number;
  speciesCount: number;
  familySlugs: string[];
}

const manifestOrders: Record<string, ManifestEntry> = {};
for (const [, entry] of orderMap) {
  manifestOrders[entry.orderId] = {
    orderId: entry.orderId,
    classSlug: entry.classSlug,
    orderSlug: entry.orderSlug,
    file: `data/orders/${entry.orderId}.json`,
    familyCount: entry.familyCount,
    speciesCount: entry.speciesCount,
    familySlugs: entry.familySlugs,
  };
}

const manifest = {
  orders: manifestOrders,
  familyToOrder,
};

writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(`  Manifest: ${Object.keys(manifestOrders).length} orders, ${Object.keys(familyToOrder).length} family → order mappings`);

// ── Build coverage summary (for CoverageModal without walking the full tree) ──
interface CoverageFamily {
  id: string;
  name: string;
  commonName?: string;
  appSlug?: string;
  className?: string;
  orderName?: string;
  portalCount: number;
  totalCount?: number;
}
interface CoverageClass {
  id: string;
  name: string;
  commonName?: string;
  families: CoverageFamily[];
}

const coverageClasses: CoverageClass[] = [];

function walkCoverage(n: TaxonNode, classes: CoverageClass[]): void {
  if (n.rank === "CLASS") {
    const cls: CoverageClass = {
      id: n.id, name: n.name, commonName: n.commonName, families: [],
    };
    classes.push(cls);
    for (const c of n.children ?? []) walkCoverage(c, classes);
    return;
  }
  if (n.rank === "FAMILY") {
    let portalCount = 0;
    function countSp(nn: TaxonNode) {
      if (nn.rank === "SPECIES") portalCount++;
      if (nn.speciesList) portalCount += nn.speciesList.length;
      for (const c of nn.children ?? []) countSp(c);
    }
    countSp(n);
    const pn = n as any;
    const last = classes[classes.length - 1];
    if (last) {
      last.families.push({
        id: n.id, name: n.name, commonName: n.commonName,
        appSlug: pn.appSlug, className: n.className, orderName: n.orderName,
        portalCount, totalCount: pn.speciesCount,
      });
    }
    return;
  }
  for (const c of n.children ?? []) walkCoverage(c, classes);
}

walkCoverage(unified, coverageClasses);
const coveragePath = resolve(portalRoot, "data/coverage-summary.json");
writeFileSync(coveragePath, JSON.stringify(coverageClasses, null, 2));
console.log(`  Coverage summary: ${coverageClasses.length} classes, ${coverageClasses.reduce((s, c) => s + c.families.length, 0)} families → data/coverage-summary.json`);

console.log(`\nDone. ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species in speciesList (${physicalCount + flatSpeciesCount} total nodes represented) → data/unified-taxonomy.json`);
