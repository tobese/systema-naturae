import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../../");
const portalRoot = resolve(__dirname, "..");

// ── Load kingdom configuration ──
interface KingdomConfig {
  label: string;
  input: string;
  rootDir: string;
  dataSuffix: string;
  colorRegistry: string;
}
interface KingdomConfigFile {
  kingdoms: Record<string, KingdomConfig>;
}
const KINGDOM = process.env.SN_KINGDOM || "";
const kingdomConfigPath = resolve(portalRoot, "data/kingdom-config.json");
let kingdomConfig: KingdomConfig | undefined;
if (existsSync(kingdomConfigPath)) {
  const allConfigs = JSON.parse(readFileSync(kingdomConfigPath, "utf-8")) as KingdomConfigFile;
  kingdomConfig = allConfigs.kingdoms[KINGDOM];
}
const kingdomRootDir = kingdomConfig?.rootDir ?? "";
const dataSuffix = kingdomConfig?.dataSuffix ?? (KINGDOM ? `-${KINGDOM}` : "");
const taxonomyInput = kingdomConfig?.input ?? process.env.SN_INPUT ?? "data/taxonomy.json";

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
  const detectedExtinct = name.startsWith("†") || /\bextinct\b/i.test(desc) || /\bfossil\b/i.test(desc);

  return {
    ...node,
    familySlug: slug,
    className: cls,
    orderName: ord,
    extinct: node.extinct !== undefined ? node.extinct : detectedExtinct,
    ...(node.fossil !== undefined ? { fossil: node.fossil } : {}),
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
    const dataPath = resolve(root, kingdomRootDir, ...parts, "src/data", `${slug}.json`);
    const cachePath = resolve(familyCacheDir, `${slug}.json`);

    let stat: ReturnType<typeof statSync> | undefined;
    try {
      stat = statSync(dataPath);
    } catch {
      // Source file missing entirely — fall through to the try/catch below,
      // which already handles/warns on this case.
    }

    if (!NO_CACHE && stat && existsSync(cachePath)) {
      try {
        const cached = JSON.parse(readFileSync(cachePath, "utf-8")) as FamilyCacheEntry;
        if (
          cached.sourceMtimeMs === stat.mtimeMs &&
          cached.sourceSize === stat.size &&
          cached.cls === (next.cls ?? "") &&
          cached.ord === (next.ord ?? "")
        ) {
          familyCacheHits++;
          // Only `children` came from the family data file; `node` (this run's
          // live taxonomy.json fields — speciesCount, commonName, etc.) must stay fresh.
          return { ...node, familySlug: slug, className: next.cls, orderName: next.ord, children: cached.children };
        }
      } catch {
        // Corrupt/unreadable cache entry — treat as a miss and regenerate below.
      }
    }

    try {
      const familyData = JSON.parse(readFileSync(dataPath, "utf-8")) as TaxonNode;
      const grafted = graftFamily(node, familyData, slug, next.cls, next.ord);
      const compressed = compressTreeNodes(grafted);
      familyCacheMisses++;
      dirtyFamilies.add(slug);
      if (stat) {
        const entry: FamilyCacheEntry = {
          sourceMtimeMs: stat.mtimeMs,
          sourceSize: stat.size,
          cls: next.cls ?? "",
          ord: next.ord ?? "",
          children: compressed.children,
        };
        writeFileSync(cachePath, JSON.stringify(entry));
      }
      return compressed;
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

// ── Build outputs: per-kingdom subdirs ──
// The skeleton/manifest/orders are what the app fetches at runtime
// (`${base}data/kingdoms/...`), so they're written under public/ where
// `vite build` copies them into dist/ verbatim. The monolithic unified tree
// and reporting files are build-time-only artifacts (used by test scripts,
// never fetched by the browser), so they stay under the private data/ dir
// to avoid bloating the production image with hundreds of MB of unused JSON.
const kingdomOutDir = resolve(portalRoot, `public/data/kingdoms/${KINGDOM || "animalia"}`);
const kingdomPrivateDir = resolve(portalRoot, `data/kingdoms/${KINGDOM || "animalia"}`);
const ORDERS_REL = `orders${dataSuffix}`;

const taxonomyPath = resolve(portalRoot, taxonomyInput);
const outputPath = resolve(kingdomPrivateDir, `unified-taxonomy.json`);
const ordersDir = resolve(kingdomOutDir, ORDERS_REL);
const skeletonPath = resolve(kingdomOutDir, `unified-taxonomy-skeleton.json`);
const manifestPath = resolve(kingdomOutDir, `order-manifest.json`);

// ── Incremental build cache ──
// Most builds only touch a handful of family data files (see git history: solo
// edits are 1-36 files/commit vs occasional bulk imports of 100-1200+). Caching
// each family's graft+compress result by source file mtime+size lets unchanged
// families skip the expensive read+stamp+compress work entirely. SN_BUILD_NO_CACHE=1
// bypasses this (CI/production builds, or debugging cache bugs).
interface FamilyCacheEntry {
  sourceMtimeMs: number;
  sourceSize: number;
  cls: string;
  ord: string;
  children?: TaxonNode[];
}
const NO_CACHE = process.env.SN_BUILD_NO_CACHE === "1";
const buildCacheDir = resolve(kingdomPrivateDir, ".build-cache");
const familyCacheDir = resolve(buildCacheDir, "families");
const buildStatePath = resolve(buildCacheDir, "state.json");
const dirtyFamilies = new Set<string>();
let familyCacheHits = 0;
let familyCacheMisses = 0;

if (!existsSync(familyCacheDir)) mkdirSync(familyCacheDir, { recursive: true });

// ── Phase timing (kept as a lightweight ongoing diagnostic — buildData.ts has a
// real history of memory/time pressure, see the repo-wide 8GB heap bump) ──
const phaseLog: Array<{ phase: string; ms: number; rssMB: number }> = [];
function timed<T>(phase: string, fn: () => T): T {
  const startMs = performance.now();
  const result = fn();
  const ms = performance.now() - startMs;
  phaseLog.push({ phase, ms: Math.round(ms), rssMB: Math.round(process.memoryUsage().rss / 1e6) });
  return result;
}

console.log(`Building kingdom ${KINGDOM || "animalia"} → ${outputPath} from ${taxonomyPath}…`);
const taxonomy = timed("read+parse taxonomy.json", () => JSON.parse(readFileSync(taxonomyPath, "utf-8")) as TaxonNode);

let taxonomyStat: ReturnType<typeof statSync> | undefined;
try {
  taxonomyStat = statSync(taxonomyPath);
} catch {
  // Shouldn't happen — taxonomy.json was just read above.
}
let taxonomyUnchanged = false;
if (!NO_CACHE && taxonomyStat && existsSync(buildStatePath)) {
  try {
    const state = JSON.parse(readFileSync(buildStatePath, "utf-8")) as { taxonomyMtimeMs: number; taxonomySize: number };
    taxonomyUnchanged = state.taxonomyMtimeMs === taxonomyStat.mtimeMs && state.taxonomySize === taxonomyStat.size;
  } catch {
    // Corrupt state file — treat as changed, safe default.
  }
}

// processTree grafts + compresses each family's subtree per-family (see the
// family cache above) instead of one global compressTreeNodes pass afterward —
// compression is purely local to each GENUS's own children, so this is
// equivalent, and it's what makes per-family caching correct/complete.
const unified = timed("processTree (graft + compress families)", () => processTree(taxonomy));
console.log(`  Family cache: ${familyCacheHits} hits, ${familyCacheMisses} misses${NO_CACHE ? " (SN_BUILD_NO_CACHE=1, cache bypassed)" : ""}`);

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
timed("count + rankCounts", () => count(unified));
unified.rankCounts = rankCounts;

// ── Ensure kingdom output directories exist ──
if (!existsSync(kingdomOutDir)) mkdirSync(kingdomOutDir, { recursive: true });
if (!existsSync(kingdomPrivateDir)) mkdirSync(kingdomPrivateDir, { recursive: true });

// ── Still produce the monolithic unified-tree for backward compat ──
// Only build-tooling reads this file (testBuild.ts, testDataContract.ts,
// classifyFossils.ts — never the running app), and re-serializing the whole
// ~600k-node tree is the single most expensive phase (~13s). So when nothing
// changed since the last successful build (no family cache misses and
// taxonomy.json itself is untouched), skip rewriting it — the file on disk is
// already correct. Any real change still pays the full re-serialize; this
// only helps the "nothing changed, just restarting" case.
const canSkipUnifiedWrite = taxonomyUnchanged && dirtyFamilies.size === 0 && existsSync(outputPath);
if (canSkipUnifiedWrite) {
  timed("write unified-taxonomy.json (skipped, unchanged)", () => {});
} else {
  timed("write unified-taxonomy.json", () => writeFileSync(outputPath, JSON.stringify(unified, null, 2)));
}
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
let ordersWritten = 0;
let ordersSkipped = 0;

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

    // Write the order data file — but only if something in it could have
    // changed: taxonomy.json itself is untouched and none of this order's
    // families were a cache miss. Otherwise the file on disk (from the last
    // build) is already correct, and re-serializing it is wasted work — this
    // is what makes editing 1-2 families cheap even though there are 383 orders.
    const orderFilePath = resolve(ordersDir, `${node.id}.json`);
    const orderDirty = !taxonomyUnchanged || familySlugs.some(slug => dirtyFamilies.has(slug)) || !existsSync(orderFilePath);
    if (orderDirty) {
      writeFileSync(orderFilePath, JSON.stringify(node, null, 2));
      ordersWritten++;
      console.log(`  Order ${node.id}: ${familySlugs.length} families, ${speciesCount} species → ${orderFilePath}`);
    } else {
      ordersSkipped++;
    }
    return;
  }

  const nextCls = node.rank === "CLASS" ? (node.name?.toLowerCase() || "") : (cls || "");
  for (const c of node.children ?? []) collectOrders(c, nextCls);
}

{
  const orderCountBefore = orderMap.size;
  timed("collectOrders (+ write order files)", () => collectOrders(unified));
  console.log(`  Extracted ${orderMap.size - orderCountBefore} order data files (${ordersWritten} written, ${ordersSkipped} unchanged/skipped)`);
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
      _dataFile: `data/kingdoms/${KINGDOM || "animalia"}/${ORDERS_REL}/${node.id}.json`,
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

const skeleton = timed("buildSkeleton", () => buildSkeleton(unified));
skeleton.rankCounts = rankCounts;

timed("write skeleton.json", () => writeFileSync(skeletonPath, JSON.stringify(skeleton, null, 2)));
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
    file: `data/kingdoms/${KINGDOM || "animalia"}/${ORDERS_REL}/${entry.orderId}.json`,
    familyCount: entry.familyCount,
    speciesCount: entry.speciesCount,
    familySlugs: entry.familySlugs,
  };
}

const manifest = {
  orders: manifestOrders,
  familyToOrder,
};

timed("write manifest.json", () => writeFileSync(manifestPath, JSON.stringify(manifest, null, 2)));
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

timed("walkCoverage", () => walkCoverage(unified, coverageClasses));
const coveragePath = resolve(kingdomPrivateDir, `coverage-summary.json`);
timed("write coverage-summary.json", () => writeFileSync(coveragePath, JSON.stringify(coverageClasses, null, 2)));
console.log(`  Coverage summary: ${coverageClasses.length} classes, ${coverageClasses.reduce((s, c) => s + c.families.length, 0)} families → ${coveragePath}`);

const buildLog = {
  timestamp: new Date().toISOString(),
  physicalNodes: physicalCount,
  compressedSpecies: flatSpeciesCount,
  totalNodes: physicalCount + flatSpeciesCount,
};
writeFileSync(resolve(kingdomPrivateDir, "build-log.json"), JSON.stringify(buildLog, null, 2) + "\n");

// Recorded last, only once every other write above has succeeded — an
// interrupted build must not leave behind a state.json that claims a clean
// build happened, or the next run would wrongly skip regenerating things.
if (taxonomyStat) {
  writeFileSync(buildStatePath, JSON.stringify({ taxonomyMtimeMs: taxonomyStat.mtimeMs, taxonomySize: taxonomyStat.size }));
}

console.log(`\nDone. ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species in speciesList (${physicalCount + flatSpeciesCount} total nodes represented) → ${outputPath}`);

console.log("\n── Phase breakdown ──");
for (const { phase, ms, rssMB } of phaseLog) {
  console.log(`  ${phase.padEnd(35)} ${String(ms).padStart(6)}ms   rss=${rssMB}MB`);
}
const totalMs = phaseLog.reduce((s, p) => s + p.ms, 0);
console.log(`  ${"total (sum of phases)".padEnd(35)} ${String(totalMs).padStart(6)}ms`);
