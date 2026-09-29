import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { resolveFamilyFile, familySourceStamp } from "./lib/familyPath.js";

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

// One authority for "where does this family's data file live", shared with
// findGaps.ts and the importers. See portal/scripts/lib/familyPath.ts for why
// this rule must not be reimplemented per script.
let resolvedFamilies = 0;
let missingFamilyFiles = 0;
const missingExamples: string[] = [];
const dataSuffix = kingdomConfig?.dataSuffix ?? (KINGDOM ? `-${KINGDOM}` : "");
// The kingdom every path is built from. An empty SN_KINGDOM means animalia,
// which the output dirs below already assume - the family resolver has to use
// the same fallback or it silently drops the kingdom segment and resolves
// taxonomy/chordata/... instead of taxonomy/animalia/chordata/... .
const effectiveKingdom = KINGDOM || "animalia";
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

function processTree(
  node: TaxonNode,
  ctx: { phylum?: string; cls?: string; ord?: string } = {},
): TaxonNode {
  let next = ctx;
  if (node.rank === "PHYLUM") next = { ...ctx, phylum: node.name.toLowerCase() };
  if (node.rank === "CLASS") next = { ...ctx, cls: node.name.toLowerCase() };
  if (node.rank === "ORDER") next = { ...ctx, ord: node.name.toLowerCase() };

  if (node.rank === "FAMILY" && node.appSlug) {
    const slug = node.appSlug as string;
    const located = resolveFamilyFile(root, {
      kingdom: effectiveKingdom,
      phylum: next.phylum,
      cls: next.cls,
      ord: next.ord,
      slug,
    });
    if (existsSync(located.file)) resolvedFamilies++;
    const dataPath = located.file;
    const stamp = familySourceStamp(root, {
      kingdom: effectiveKingdom,
      phylum: next.phylum, cls: next.cls, ord: next.ord, slug,
    });
    if (stamp.size < 0) {
      missingFamilyFiles++;
      if (missingExamples.length < 8) missingExamples.push(dataPath);
    }
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
        // stamp.phylum/stamp.layout are part of the key on purpose: if a family
        // moves to the kingdom-first layout and the key does not change with it,
        // the moved file silently reuses a stale graft. Wrong species, no error.
        if (
          cached.sourceMtimeMs === stat.mtimeMs &&
          cached.sourceSize === stat.size &&
          cached.cls === (next.cls ?? "") &&
          cached.ord === (next.ord ?? "") &&
          (cached.phylum ?? "") === stamp.phylum &&
          (cached.layout ?? "") === stamp.layout
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
          phylum: stamp.phylum,
          layout: stamp.layout,
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
const kingdomOutDir = resolve(portalRoot, `public/data/kingdoms/${effectiveKingdom}`);
const kingdomPrivateDir = resolve(portalRoot, `data/kingdoms/${effectiveKingdom}`);
const ORDERS_REL = `orders${dataSuffix}`;

const taxonomyPath = resolve(portalRoot, taxonomyInput);
const outputPath = resolve(kingdomPrivateDir, `unified-taxonomy.json`);
const ordersDir = resolve(kingdomOutDir, ORDERS_REL);
// The graph reads these instead of the order files. Separate directory rather
// than a suffix on the file name so the existing manifest `file` field keeps
// meaning "the full order", and so a stale nav file from an older build can
// never be mistaken for a current one (the dirty check covers that too).
const navOrdersRel = `orders-nav${dataSuffix}`;
const navOrdersDir = resolve(kingdomOutDir, navOrdersRel);
// The graph's order file: the order tree with species prose removed and
// everything else intact. The book keeps the full-prose `orders/` above,
// because SpeciesEntry renders species.description from it.
const namesOrdersRel = `orders-names${dataSuffix}`;
const namesOrdersDir = resolve(kingdomOutDir, namesOrdersRel);
// Per-genus species prose, fetched when a reader opens a genus.
const proseRel = `orders-prose${dataSuffix}`;
const proseDir = resolve(kingdomOutDir, proseRel);
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
  phylum?: string;
  layout?: string;
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

console.log(`Building kingdom ${effectiveKingdom} → ${outputPath} from ${taxonomyPath}…`);
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

// ── The monolithic unified tree is opt-in ──
// It is 316MB for plantae, and one dirty family out of 1022 forces a full
// JSON.stringify of all 346k nodes: ~3.2s and +1.7GB RSS. That buys a file
// the browser never fetches — the app reads the skeleton plus the per-order
// files — which only testBuild.ts and testDataContract.ts consume, and which
// the Dockerfile excludes from the build context anyway. Measured on plantae:
//
//   clean rebuild    2.4s,  454MB RSS   nothing written
//   one family edit  5.7s, 2.1GB RSS   full re-serialize
//
// So SN_BUILD_UNIFIED=1 opts in. Skipping the write leaves whatever is on
// disk, which may now be stale, and a stale monolith that the tests validate
// without complaint is exactly the silent success this build has been
// hardened against — so the freshness is recorded in state.json, printed
// here, and asserted by testDataContract.ts instead of being inferred from
// the file merely existing.
const WRITE_UNIFIED = process.env.SN_BUILD_UNIFIED === "1";
const unifiedWasCurrent = taxonomyUnchanged && dirtyFamilies.size === 0 && existsSync(outputPath);
if (WRITE_UNIFIED) {
  timed("write unified-taxonomy.json", () => writeFileSync(outputPath, JSON.stringify(unified, null, 2)));
} else {
  timed("write unified-taxonomy.json (opt-in: SN_BUILD_UNIFIED=1)", () => {});
}
console.log(`  Unified tree: ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species`);
if (!WRITE_UNIFIED) {
  console.log(
    `  ${unifiedWasCurrent ? "unchanged on disk" : "STALE, not rewritten"}` +
    ` — opt-in rebuild with SN_BUILD_UNIFIED=1`,
  );
}

// ── Extract per-order subtrees ──
if (!existsSync(ordersDir)) mkdirSync(ordersDir, { recursive: true });
if (!existsSync(navOrdersDir)) mkdirSync(navOrdersDir, { recursive: true });
if (!existsSync(namesOrdersDir)) mkdirSync(namesOrdersDir, { recursive: true });
if (!existsSync(proseDir)) mkdirSync(proseDir, { recursive: true });

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
let navOrdersWritten = 0;
let namesOrdersWritten = 0;
let genusProseWritten = 0;

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

    // The nav tier: the same order with species prose and speciesList removed,
    // so the graph can lay the order out without parsing the full file. The
    // graph draws minimally-described species as pruned dots, so it needs
    // structure and counts, not the 300MB of prose that sits under them.
    // Measured across the six kingdoms: 442.6MB -> 29.5MB, and the worst
    // single file 52.6MB (COLEOPTERA) -> 4.3MB. See docs/data-tiers.md.
    //
    // Same dirty rule as the order file, so the two can never disagree about
    // which build they came from.
    const navFilePath = resolve(navOrdersDir, `${node.id}.json`);
    if (orderDirty || !existsSync(navFilePath)) {
      writeFileSync(navFilePath, JSON.stringify(navProjection(node), null, 2));
      navOrdersWritten++;
    }

    // The names tier: everything the order file has except species prose. This
    // is the graph's order file. It cannot be the nav tier, because SearchBox
    // indexes name and commonName across children *and* speciesList, and the
    // Eponyms and Species-of-the-Day modals read namedAfter off the same tree -
    // a projection without species records silently loses search over 110,614
    // of animalia's 527,630 species.
    //
    // Descriptions are the 63% of the bytes (animalia: ~130MB of 209MB), and
    // the graph only needs the description of a species a reader actually
    // opens. So they move to per-genus files, written below.
    const namesFilePath = resolve(namesOrdersDir, `${node.id}.json`);
    if (orderDirty || !existsSync(namesFilePath)) {
      writeFileSync(namesFilePath, JSON.stringify(namesProjection(node), null, 2));
      namesOrdersWritten++;
    }
    // `|| !existsSync(...)` for the same reason as the nav tier above: a clean
    // order whose prose directory was never created would otherwise stay empty
    // forever, because nothing else would ever mark it dirty.
    if (orderDirty || !existsSync(resolve(proseDir, node.id))) writeGenusProse(node);
    return;
  }

  const nextCls = node.rank === "CLASS" ? (node.name?.toLowerCase() || "") : (cls || "");
  for (const c of node.children ?? []) collectOrders(c, nextCls);
}

function speciesOf(genus: TaxonNode): TaxonNode[] {
  return [
    ...(genus.speciesList ?? []),
    ...(genus.children ?? []).filter(c => c.rank === "SPECIES"),
  ];
}

/**
 * One file per genus that has prose worth reading, holding that genus's
 * species at full fidelity. Fetched when a reader opens the genus, so the cost
 * of prose is paid for the genus being read rather than for the whole order.
 *
 * Only 38% of animalia's genera (21,588 of 57,161) have any described species,
 * and the median genus prose file is 1KB against a 1.1MB worst case
 * (Pheidole) - so the file count is high but the bytes are not, and nothing is
 * fetched at all unless a genus is opened.
 *
 * A genus that loses its last description keeps a stale file until the next
 * dirty rebuild rewrites the order. That is deliberate: an empty response is
 * indistinguishable from "no prose", whereas a file that outlives its data
 * would show a description the family no longer has.
 */
function writeGenusProse(order: TaxonNode): void {
  // Only called for a dirty order: 21,588 writes on an otherwise clean build is
  // exactly the cost the dirty check exists to avoid.
  const dir = resolve(proseDir, order.id);
  let wrote = 0;
  // Genera sit under FAMILY (and sometimes SUBFAMILY), not directly under the
  // order, so this has to walk down rather than look at order.children.
  const walk = (node: TaxonNode) => {
    for (const child of node.children ?? []) {
      if (child.rank === "GENUS") {
        const species = speciesOf(child);
        if (!species.some(s => (s.description ?? "").trim())) continue;
        if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
        writeFileSync(
          resolve(dir, `${child.id}.json`),
          JSON.stringify({ genus: child.id, name: child.name, order: order.id, species }, null, 2),
        );
        wrote++;
        continue;
      }
      walk(child);
    }
  };
  walk(order);
  genusProseWritten += wrote;
}

/**
 * The graph's order file: structure, names, family/genus prose, and per-species
 * facts. Two things come out.
 *
 * `description` moves to orders-prose/, fetched when a genus is opened.
 *
 * The class/order/family stamps move *out* rather than out of the file:
 * they are constant for the family or genus a species sits under, and repeated
 * on all 527,630 animalia species they are 16MB of every large order file. The
 * client re-derives them by walking down - useTaxonomyLoader's inheritStamps -
 * and the contract suite checks the result against the full order files, so
 * this cannot quietly produce a wrong colour or a search result that navigates
 * to the wrong family.
 *
 * `rank` is kept. It is read 79 times across the graph and is implied by
 * position, which is a poor substitute for an explicit value; it is 5% of the
 * bytes and not worth the regression surface.
 */
// `lineage` is deliberately NOT here. It is usually the genus, but not always -
// 379 animalia nodes have no lineage at all - so re-deriving it would invent a
// value the source does not have, and the check that compares the inherited tree
// against the full order file caught exactly that. Keeping it costs 7% of the
// bytes and makes the change provably behaviour-neutral.
const INHERITED_SPECIES_FIELDS = ["className", "orderName", "familySlug"] as const;

/**
 * Drop one stamp so the client can re-derive it from its ancestors.
 *
 * Only a real value is dropped. An explicit `null` is left in place: the client
 * fills a *missing* field, so deleting a null one would have it re-derive a
 * value the source deliberately does not have. 380 animalia breed nodes carry
 * `lineage: null`, and a check that compares the inherited tree against the
 * full order file caught exactly that.
 */
function dropInheritable(lean: Record<string, unknown>): void {
  for (const f of INHERITED_SPECIES_FIELDS) {
    if (lean[f] != null) delete lean[f];
  }
}

function namesProjection(node: TaxonNode): TaxonNode {
  const children: TaxonNode[] = [];
  for (const child of node.children ?? []) {
    if (child.rank === "SPECIES") {
      const lean: Record<string, unknown> = { ...child };
      delete lean.description;
      dropInheritable(lean);
      children.push(lean as TaxonNode);
      continue;
    }
    if (child.rank === "GENUS") {
      // The genus keeps its own stamps: it is the thing a reader opens, and
      // there are 57,161 of them against 527,630 species.
      const genus = { ...child, speciesList: undefined } as TaxonNode;
      if (child.speciesList) {
        genus.speciesList = child.speciesList.map(sp => {
          const lean: Record<string, unknown> = { ...sp };
          delete lean.description;
          dropInheritable(lean);
          return lean as TaxonNode;
        });
      }
      children.push(genus);
      continue;
    }
    children.push(namesProjection(child));
  }
  return { ...node, children, speciesList: undefined } as TaxonNode;
}

/**
 * Structure and counts only. FAMILY and GENUS keep their prose and stamps,
 * because the info panel renders them; SPECIES reduce to {id, name, rank},
 * which is all the tree needs to draw a node and all the Eponyms/species
 * lookups need to find one. A genus records how many species it holds and how
 * many of those are described, so the graph can show coverage without the
 * species themselves.
 */
function navProjection(node: TaxonNode): TaxonNode {
  const out: TaxonNode = { ...node };
  delete out.speciesList;

  const children: TaxonNode[] = [];
  for (const child of node.children ?? []) {
    if (child.rank === "SPECIES") {
      children.push({ id: child.id, name: child.name, rank: "SPECIES" } as TaxonNode);
      continue;
    }
    if (child.rank === "GENUS") {
      let total = 0;
      let described = 0;
      const count = (n: TaxonNode) => {
        if (n.rank === "SPECIES") {
          total++;
          if (n.description) described++;
        }
        for (const s of n.speciesList ?? []) {
          total++;
          if (s.description) described++;
        }
        for (const c of n.children ?? []) count(c);
      };
      for (const c of child.children ?? []) count(c);
      for (const s of child.speciesList ?? []) {
        total++;
        if (s.description) described++;
      }
      // Rebuilt field by field, never spread. Spreading `{...child}` keeps the
      // genus's own `children`, which is every species node under it with its
      // full description - 25MB for COLEOPTERA instead of 4MB, and the whole
      // tier collapses to 102MB instead of 17.8MB.
      children.push({
        id: child.id,
        name: child.name,
        rank: "GENUS",
        description: child.description,
        commonName: child.commonName,
        lineage: child.lineage,
        familySlug: child.familySlug,
        className: child.className,
        orderName: child.orderName,
        extinct: child.extinct,
        _speciesCount: total,
        _describedCount: described,
      } as TaxonNode);
      continue;
    }
    children.push(navProjection(child));
  }
  out.children = children;
  return out;
}

{
  const orderCountBefore = orderMap.size;
  timed("collectOrders (+ write order files)", () => collectOrders(unified));
  console.log(`  Extracted ${orderMap.size - orderCountBefore} order data files (${ordersWritten} written, ${ordersSkipped} unchanged/skipped)`);
  console.log(`  Nav tier: ${navOrdersWritten} written → ${navOrdersDir}`);
  console.log(`  Names tier: ${namesOrdersWritten} written → ${namesOrdersDir}`);
  console.log(`  Genus prose: ${genusProseWritten} genus files → ${proseDir}`);
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
  navFile: string;
  namesFile: string;
  proseDir: string;
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
    // Structure-and-counts projection of the same order. The graph loads this
    // to lay an order out; `file` is only fetched when a reader actually opens
    // something and needs the prose. See docs/data-tiers.md.
    navFile: `data/kingdoms/${KINGDOM || "animalia"}/${navOrdersRel}/${entry.orderId}.json`,
    // The graph's order file: names and structure, no species prose. The book's
    // is `file`, which keeps it.
    namesFile: `data/kingdoms/${KINGDOM || "animalia"}/${namesOrdersRel}/${entry.orderId}.json`,
    // Per-genus species descriptions, fetched when a genus is opened.
    proseDir: `data/kingdoms/${KINGDOM || "animalia"}/${proseRel}/${entry.orderId}`,
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
  writeFileSync(buildStatePath, JSON.stringify({
    taxonomyMtimeMs: taxonomyStat.mtimeMs,
    taxonomySize: taxonomyStat.size,
    // Whether the monolith on disk still matches this build. Absent means the
    // build never opted in, so a consumer cannot mistake a leftover file from
    // an older build for a current one.
    unified: WRITE_UNIFIED || unifiedWasCurrent ? "current" : "stale",
  }));
}

console.log(`\nDone. ${physicalCount} physical nodes, ${flatSpeciesCount} compressed flat species in speciesList (${physicalCount + flatSpeciesCount} total nodes represented) → ${outputPath}`);

console.log("\n── Phase breakdown ──");
for (const { phase, ms, rssMB } of phaseLog) {
  console.log(`  ${phase.padEnd(35)} ${String(ms).padStart(6)}ms   rss=${rssMB}MB`);
}
const totalMs = phaseLog.reduce((s, p) => s + p.ms, 0);
console.log(`  ${"total (sum of phases)".padEnd(35)} ${String(totalMs).padStart(6)}ms`);

// ── Layout + completeness report ────────────────────────────────────────────
// A family whose data file cannot be found produces no children and no error:
// the graft is simply skipped. At 8k families that is invisible in a wall of
// console.warn lines, and a run that found nothing still exits 0. So the counts
// are printed, and a missing-file total is fatal.
console.log(`\n── Family data layout ──`);
console.log(`  ${"resolved".padEnd(15)} ${String(resolvedFamilies).padStart(6)}  (taxonomy/${effectiveKingdom}/…)`);
const declared = resolvedFamilies + missingFamilyFiles;
if (missingFamilyFiles > 0) {
  console.log(`  ${"no data file".padEnd(15)} ${String(missingFamilyFiles).padStart(6)}  ` +
    `(${declared} declared; these graft empty)`);
  for (const ex of missingExamples) console.log(`      ${ex}`);
}
// A family whose file exists but that the resolver cannot reach is a path bug,
// and it is completely silent: the graft is skipped, nothing is thrown, exit 0.
// A partial count is normal - the taxonomy declares more families than have data
// (plantae: 1,259 declared, 1,021 with files). A *total* failure means the
// resolver itself is wrong, so that aborts.
if (declared > 0 && resolvedFamilies === 0) {
  console.error(
    `\nERROR: none of ${missingFamilyFiles} family data files resolved.\n` +
    `Every family in ${effectiveKingdom} grafted empty, which means the path\n` +
    `resolver is broken rather than the data being absent. Aborting.`,
  );
  process.exit(1);
}
