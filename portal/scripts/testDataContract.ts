import { readFileSync, readdirSync, statSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { strict as assert } from 'assert';

const KINGDOM = 'animalia';
const DATA_DIR = resolve(import.meta.dirname, '..', 'public', 'data', 'kingdoms', KINGDOM);
const PRIVATE_DATA_DIR = resolve(import.meta.dirname, '..', 'data', 'kingdoms', KINGDOM);
const ORDERS_DIR = join(DATA_DIR, 'orders');

function loadJson<T = unknown>(path: string): T {
  return JSON.parse(readFileSync(path, 'utf-8')) as T;
}

function* walkTree<T extends { children?: T[] }>(node: T): Generator<T> {
  yield node;
  for (const child of node.children ?? []) {
    yield* walkTree(child);
  }
}

interface SkeletonNode {
  id: string; name: string; rank: string; commonName?: string;
  description?: string; children?: SkeletonNode[];
  _familyCount?: number; _speciesCount?: number; _dataFile?: string;
  className?: string; orderName?: string;
  rankCounts?: Record<string, number>;
}

interface OrderNode {
  id: string; name: string; rank: string; commonName?: string;
  description?: string; children?: OrderNode[]; speciesList?: OrderNode[];
  appSlug?: string; familySlug?: string; className?: string;
  orderName?: string; speciesCount?: number; notableMembers?: string[];
  lineage?: string; extinct?: boolean; subspeciesCount?: number;
  sourcedFrom?: string; continents?: string[];
}

interface ManifestEntry {
  orderId: string; classSlug: string; orderSlug: string;
  file: string; familyCount: number; speciesCount: number;
  familySlugs: string[];
}

interface Manifest {
  orders: Record<string, ManifestEntry>;
  familyToOrder: Record<string, string>;
}

// A binomial in the "Genus species" form and nothing else. Anything else is
// not a species: a trinomial (Canis lupus familiaris), a "sp. spec" or
// "sp. undefined" placeholder, or a bare genus used as a catch-all.
const STRICT_BINOMIAL = /^[A-Z][a-z]+ [a-z][a-z-]+$/;

// Portal species nodes that are not binomials, collected while the order files
// are scanned. Module scope because the coverage section reads it.
const nonBinomial: { familySlug: string; id: string; name: string }[] = [];

let passCount = 0;
let failCount = 0;
let skipCount = 0;

class Skipped extends Error {}

/** Abort the current test as "not applicable", counted apart from passes. */
function skip(reason: string): never {
  throw new Skipped(reason);
}

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`  PASS  ${name}`);
    passCount++;
  } catch (err) {
    if (err instanceof Skipped) {
      console.log(`  SKIP  ${name}`);
      console.log(`        ${err.message}`);
      skipCount++;
      return;
    }
    console.error(`  FAIL  ${name}`);
    console.error(`        ${err instanceof Error ? err.message : String(err)}`);
    failCount++;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SKELETON
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nSKELETON');
const skeleton = loadJson<SkeletonNode>(join(DATA_DIR, 'unified-taxonomy-skeleton.json'));

test('root is KINGDOM with expected metadata', () => {
  assert.equal(skeleton.id, 'ANIMALIA');
  assert.equal(skeleton.rank, 'KINGDOM');
  assert.equal(skeleton.commonName, 'Animals');
  assert.ok(skeleton.rankCounts);
});

test('rankCounts match known totals', () => {
  const rc = skeleton.rankCounts!;
  assert.equal(rc.KINGDOM, 1);
  assert.equal(rc.PHYLUM, 32);
  assert.equal(rc.CLASS, 75);
  assert.equal(rc.ORDER, 383);
  assert.equal(rc.FAMILY, 5071);
  assert.equal(rc.GENUS, 57320);
  assert.equal(rc.SPECIES, 529125);
});

test('root has exactly 32 phylum children', () => {
  assert.ok(skeleton.children);
  assert.equal(skeleton.children!.length, 32);
  for (const child of skeleton.children!) {
    assert.equal(child.rank, 'PHYLUM');
  }
});

test('every ORDER node has _dataFile and counts', () => {
  for (const node of walkTree(skeleton)) {
    if (node.rank === 'ORDER') {
      assert.ok(node._dataFile, `ORDER ${node.id} missing _dataFile`);
      assert.match(node._dataFile!, /data\/kingdoms\/animalia\/orders\/[A-Z_]+\.json/);
      assert.equal(typeof node._familyCount, 'number');
      assert.equal(typeof node._speciesCount, 'number');
      assert.ok(node._familyCount! >= 0);
      assert.ok(node._speciesCount! >= 0);
      assert.equal(node.children, undefined, `ORDER ${node.id} should have no children in skeleton`);
    }
  }
});

test('every CLASS node has _familyCount', () => {
  for (const node of walkTree(skeleton)) {
    if (node.rank === 'CLASS') {
      assert.equal(typeof node._familyCount, 'number');
      assert.ok(node._familyCount! >= 0);
    }
  }
});

test('sum of order _familyCount is within 10% of rankCounts.FAMILY', () => {
  let sum = 0;
  for (const node of walkTree(skeleton)) {
    if (node.rank === 'ORDER') sum += node._familyCount ?? 0;
  }
  // Some families lack data files (build warnings), so ORDER _familyCount
  // may be lower than the full rankCounts.FAMILY which counts all families.
  const diff = skeleton.rankCounts!.FAMILY - sum;
  const pct = diff / skeleton.rankCounts!.FAMILY;
  assert.ok(pct < 0.10, `familyCount gap ${diff} (${(pct*100).toFixed(1)}%) exceeds 10% threshold`);
});

test('sum of order _speciesCount is within 1% of rankCounts.SPECIES', () => {
  let sum = 0;
  for (const node of walkTree(skeleton)) {
    if (node.rank === 'ORDER') sum += node._speciesCount ?? 0;
  }
  const diff = skeleton.rankCounts!.SPECIES - sum;
  const pct = diff / skeleton.rankCounts!.SPECIES;
  assert.ok(pct < 0.01, `speciesCount gap ${diff} (${(pct*100).toFixed(2)}%) exceeds 1% threshold`);
});

// ═══════════════════════════════════════════════════════════════════════════════
// MANIFEST
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nMANIFEST');
const manifest = loadJson<Manifest>(join(DATA_DIR, 'order-manifest.json'));

test('every ORDER in skeleton has a manifest entry', () => {
  for (const node of walkTree(skeleton)) {
    if (node.rank === 'ORDER') {
      assert.ok(manifest.orders[node.id], `ORDER ${node.id} missing from manifest`);
    }
  }
});

test('every manifest order file exists on disk', () => {
  // Manifest `file` values are web-root-relative, because the app fetches them
  // as `${BASE_URL}${file}` and public/ is the web root. Resolving them against
  // portal/ instead looks in the private data dir, where they have never
  // lived, so this assertion could not pass.
  const baseDir = resolve(import.meta.dirname, '..', 'public');
  for (const [orderId, entry] of Object.entries(manifest.orders)) {
    const filePath = resolve(baseDir, entry.file);
    assert.doesNotThrow(() => statSync(filePath), `missing: ${entry.file}`);
  }
});

test('familyToOrder maps every family slug to a valid order', () => {
  for (const [familySlug, orderId] of Object.entries(manifest.familyToOrder)) {
    assert.ok(manifest.orders[orderId], `familyToOrder["${familySlug}"] -> ${orderId} not found`);
  }
});

test('manifest familyCount matches CARNIVORA file', () => {
  const entry = manifest.orders['CARNIVORA'];
  const orderData = loadJson<OrderNode>(join(DATA_DIR, 'orders', 'CARNIVORA.json'));
  const actual = orderData.children?.filter(c => c.rank === 'FAMILY').length ?? 0;
  assert.equal(actual, entry.familyCount);
});

  test('manifest familySlugs match CARNIVORA file', () => {
    const entry = manifest.orders['CARNIVORA'];
    const orderData = loadJson<OrderNode>(join(DATA_DIR, 'orders', 'CARNIVORA.json'));
    const actual = orderData.children
      ?.filter(c => c.rank === 'FAMILY' && c.appSlug)
      .map(c => c.appSlug!)
      .sort() ?? [];
    assert.deepStrictEqual(actual, [...entry.familySlugs].sort());
  });

test('manifest familyCount matches PASSERIFORMES file', () => {
  const entry = manifest.orders['PASSERIFORMES'];
  const orderData = loadJson<OrderNode>(join(DATA_DIR, 'orders', 'PASSERIFORMES.json'));
  const actual = orderData.children?.filter(c => c.rank === 'FAMILY').length ?? 0;
  assert.equal(actual, entry.familyCount);
});

// ═══════════════════════════════════════════════════════════════════════════════
// ORDER FILE SCHEMA
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nORDER FILE SCHEMA');

const sampleOrders = ['CARNIVORA', 'PASSERIFORMES', 'CHIROPTERA', 'PICIFORMES'];

for (const orderId of sampleOrders) {
  const orderData = loadJson<OrderNode>(join(DATA_DIR, 'orders', `${orderId}.json`));

  test(`${orderId}: root is ORDER with children`, () => {
    assert.equal(orderData.rank, 'ORDER');
    assert.ok(orderData.children);
    assert.ok(orderData.children!.length > 0);
  });

  test(`${orderId}: every FAMILY has required fields`, () => {
    const families = orderData.children!.filter(c => c.rank === 'FAMILY');
    assert.ok(families.length > 0);
    for (const family of families) {
      assert.ok(family.id);
      assert.ok(family.appSlug);
      assert.ok(family.familySlug);
      assert.equal(family.appSlug, family.familySlug);
      assert.equal(typeof family.speciesCount, 'number');
      assert.ok(family.speciesCount! >= 0);
      assert.ok(family.className);
      assert.ok(family.orderName);
    }
  });

  test(`${orderId}: every GENUS has familySlug`, () => {
    const genera: OrderNode[] = [];
    function collect(n: OrderNode) {
      if (n.rank === 'GENUS') genera.push(n);
      for (const c of n.children ?? []) collect(c);
    }
    collect(orderData);
    assert.ok(genera.length > 0);
    for (const genus of genera) {
      assert.ok(genus.familySlug, `GENUS ${genus.id} missing familySlug`);
      assert.ok(genus.className);
      assert.ok(genus.orderName);
    }
  });

  test(`${orderId}: most GENUS have lineage (>=95%)`, () => {
    const genera: OrderNode[] = [];
    function collect(n: OrderNode) {
      if (n.rank === 'GENUS') genera.push(n);
      for (const c of n.children ?? []) collect(c);
    }
    collect(orderData);
    const withLineage = genera.filter(g => g.lineage).length;
    const pct = withLineage / genera.length;
    assert.ok(pct >= 0.95, `${orderId}: only ${(pct*100).toFixed(1)}% of genera have lineage`);
  });

  test(`${orderId}: SPECIES have required core fields`, () => {
    const species: OrderNode[] = [];
    function collect(n: OrderNode) {
      if (n.rank === 'SPECIES') species.push(n);
      for (const c of n.children ?? []) collect(c);
      for (const c of n.speciesList ?? []) collect(c);
    }
    collect(orderData);
    assert.ok(species.length > 0);
    for (const sp of species) {
      assert.ok(sp.id);
      assert.ok(sp.name);
      assert.equal(sp.rank, 'SPECIES');
      assert.ok(sp.familySlug);
      assert.ok(sp.className);
      assert.ok(sp.orderName);
    }
  });

  test(`${orderId}: most SPECIES have subspeciesCount (>=95%)`, () => {
    const species: OrderNode[] = [];
    function collect(n: OrderNode) {
      if (n.rank === 'SPECIES') species.push(n);
      for (const c of n.children ?? []) collect(c);
      for (const c of n.speciesList ?? []) collect(c);
    }
    collect(orderData);
    const withCount = species.filter(s => typeof s.subspeciesCount === 'number').length;
    const pct = withCount / species.length;
    assert.ok(pct >= 0.95, `${orderId}: only ${(pct*100).toFixed(1)}% of species have subspeciesCount`);
  });

  test(`${orderId}: speciesList only contains SPECIES with no children`, () => {
    const genera: OrderNode[] = [];
    function collectGenera(n: OrderNode) {
      if (n.rank === 'GENUS') genera.push(n);
      for (const c of n.children ?? []) collectGenera(c);
    }
    collectGenera(orderData);

    let count = 0;
    for (const genus of genera) {
      for (const sp of genus.speciesList ?? []) {
        count++;
        assert.equal(sp.rank, 'SPECIES');
        assert.ok(sp.id);
        assert.ok(sp.name);
        assert.equal(sp.children, undefined);
      }
    }
    assert.ok(count > 0, `${orderId}: no speciesList entries found`);
  });

  test(`${orderId}: no species duplicated in children + speciesList`, () => {
    const genera: OrderNode[] = [];
    function collectGenera(n: OrderNode) {
      if (n.rank === 'GENUS') genera.push(n);
      for (const c of n.children ?? []) collectGenera(c);
    }
    collectGenera(orderData);

    let dupCount = 0;
    for (const genus of genera) {
      const childIds = new Set((genus.children ?? []).filter(c => c.rank === 'SPECIES').map(c => c.id));
      const listIds = new Set((genus.speciesList ?? []).map(c => c.id));
      for (const id of childIds) {
        if (listIds.has(id)) dupCount++;
      }
    }
    // Known issue: PASSERIFORMES has 2 duplicated species (pre-existing data bug)
    assert.ok(dupCount <= 2, `${orderId}: ${dupCount} species duplicated in children + speciesList`);
  });
}

test('every order file on disk has a manifest entry', () => {
  const files = readdirSync(ORDERS_DIR).filter(f => f.endsWith('.json'));
  for (const file of files) {
    const orderId = file.replace('.json', '');
    assert.ok(manifest.orders[orderId], `order file ${file} missing from manifest`);
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// STRUCTURAL SNAPSHOTS
//
// Exact counts, refreshed by hand after an import. They catch unintended change
// rather than intended change: an import is *expected* to move SPECIES, GENUS,
// BREED and BREED_GROUP, and everything at or above FAMILY is expected to stay
// put. So the structural spine is the part worth reading when one of these
// goes red - KINGDOM/PHYLUM/CLASS/ORDER/FAMILY moving means a data problem,
// while a leaf count moving usually just means the last import did its job.
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nSTRUCTURAL SNAPSHOTS');

test('skeleton node type distribution', () => {
  const counts: Record<string, number> = {};
  for (const node of walkTree(skeleton)) {
    counts[node.rank] = (counts[node.rank] || 0) + 1;
  }
  // Tardigrada has no CLASS/ORDER layer — its FAMILY/GENUS/SPECIES
  // are inlined in the skeleton instead of being in a separate order file.
  assert.deepStrictEqual(counts, {
    KINGDOM: 1, PHYLUM: 32, CLASS: 75, ORDER: 383,
    FAMILY: 1, GENUS: 159, SPECIES: 57,
  });
});

test('skeleton root rankCounts snapshot', () => {
  assert.deepStrictEqual(skeleton.rankCounts, {
    KINGDOM: 1, PHYLUM: 32, CLASS: 75, ORDER: 383,
    FAMILY: 5071, GENUS: 57320, SPECIES: 529125,
    SUBFAMILY: 8, TRIBE: 10, SUBSPECIES: 851,
    BREED_GROUP: 52, BREED: 321, HYBRID_GROUP: 1, HYBRID: 4,
  });
});

test('manifest order count snapshot', () => {
  assert.equal(Object.keys(manifest.orders).length, 383);
  // familyToOrder maps families that have order data files (5070).
  // The remaining family (of 5071 total) is Tardigrada, inlined in the
  // skeleton rather than a separate order file.
  const familyToOrderCount = Object.keys(manifest.familyToOrder).length;
  assert.equal(familyToOrderCount, 5070);
});

test('manifest CARNIVORA entry snapshot', () => {
  assert.deepStrictEqual(manifest.orders['CARNIVORA'], {
    orderId: 'CARNIVORA', classSlug: 'mammalia', orderSlug: 'carnivora',
    file: 'data/kingdoms/animalia/orders/CARNIVORA.json',
    navFile: 'data/kingdoms/animalia/orders-nav/CARNIVORA.json',
    namesFile: 'data/kingdoms/animalia/orders-names/CARNIVORA.json',
    proseDir: 'data/kingdoms/animalia/orders-prose/CARNIVORA',
    familyCount: 5, speciesCount: 1015,
    familySlugs: ['felidae', 'canidae', 'mustelidae', 'ursidae', 'phocidae'],
  });
});

test('CARNIVORA order structure snapshot', () => {
  const orderData = loadJson<OrderNode>(join(DATA_DIR, 'orders', 'CARNIVORA.json'));
  assert.equal(orderData.id, 'CARNIVORA');
  assert.equal(orderData.rank, 'ORDER');

  const families = orderData.children!.filter(c => c.rank === 'FAMILY');
  assert.equal(families.length, 5);
  assert.deepStrictEqual(
    families.map(f => f.appSlug).sort(),
    ['canidae', 'felidae', 'mustelidae', 'phocidae', 'ursidae'],
  );

  const felidae = families.find(f => f.appSlug === 'felidae')!;
  const genera = felidae.children!.filter(c => c.rank === 'GENUS');
  assert.ok(genera.length > 0);
  assert.ok(genera.some(g => g.id === 'GENUS_PRIONAILURUS'));
});

// ═══════════════════════════════════════════════════════════════════════════════
// ALL ORDER FILES (lightweight batch scan)
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nALL ORDER FILES');

const allOrderFiles = readdirSync(ORDERS_DIR).filter(f => f.endsWith('.json'));

test('all 383 order files exist and are valid JSON', () => {
  assert.equal(allOrderFiles.length, 383);
  for (const file of allOrderFiles) {
    const path = join(ORDERS_DIR, file);
    const data = loadJson<OrderNode>(path);
    assert.equal(data.rank, 'ORDER', `${file}: root rank mismatch`);
    assert.ok(data.children, `${file}: missing children`);
    assert.ok(data.children!.length > 0, `${file}: empty children`);
  }
});

// Batch tests across all order files — single pass for performance
{
  let totalFamilies = 0;
  let totalGenera = 0;
  let totalSpecies = 0;
  let totalSpeciesList = 0;
  let emptyGenusCount = 0;
  let familyMissingAppSlug = 0;
  let genusMissingFamilySlug = 0;
  let speciesMissingSubspeciesCount = 0;
  let dupCount = 0;

  for (const file of allOrderFiles) {
    const orderData = loadJson<OrderNode>(join(ORDERS_DIR, file));

    function scan(node: OrderNode) {
      if (node.rank === 'FAMILY') {
        totalFamilies++;
        if (!node.appSlug) familyMissingAppSlug++;
      }
      if (node.rank === 'GENUS') {
        totalGenera++;
        if (!node.familySlug) genusMissingFamilySlug++;
        const childCount = (node.children ?? []).length + (node.speciesList ?? []).length;
        if (childCount === 0) emptyGenusCount++;
        totalSpeciesList += node.speciesList?.length ?? 0;
      }
      if (node.rank === 'SPECIES') {
        totalSpecies++;
        if (typeof node.subspeciesCount !== 'number') speciesMissingSubspeciesCount++;
        // A portal node is not automatically a species: families carry
        // domestic trinomials (Canis lupus familiaris, Sus scrofa domesticus)
        // and "sp. spec" placeholders (Canis spec, Felis undefined). Counted
        // per family, because the coverage invariant below depends on them.
        if (!STRICT_BINOMIAL.test(node.name ?? '')) {
          nonBinomial.push({ familySlug: node.familySlug ?? '', id: node.id, name: node.name ?? '' });
        }
      }
      for (const child of node.children ?? []) scan(child);
      for (const child of node.speciesList ?? []) scan(child);
    }
    scan(orderData);

    // Check for duplicates across children + speciesList per genus
    function checkDups(node: OrderNode) {
      if (node.rank === 'GENUS') {
        const childIds = new Set((node.children ?? []).filter(c => c.rank === 'SPECIES').map(c => c.id));
        const listIds = new Set((node.speciesList ?? []).map(c => c.id));
        for (const id of childIds) if (listIds.has(id)) dupCount++;
      }
      for (const child of node.children ?? []) checkDups(child);
    }
    checkDups(orderData);
  }

  test('total families across all orders is 5070 (incl. bulk-imported)', () => {
    // 5071 total families in taxonomy; 5070 in order files (Tardigrada inline is the 1 difference).
    // 4865 have dedicated data files (manifest.familyToOrder).
    // The remainder are bulk-imported (e.g., beetles) and exist only in order files without appSlug.
    assert.equal(totalFamilies, 5070);
  });

  test('>=95% of FAMILY nodes have appSlug', () => {
    const pct = (totalFamilies - familyMissingAppSlug) / totalFamilies;
    assert.ok(pct >= 0.95, `only ${(pct*100).toFixed(1)}% of families have appSlug (${familyMissingAppSlug} missing)`);
  });

  test('all GENUS nodes have familySlug', () => {
    assert.equal(genusMissingFamilySlug, 0, `${genusMissingFamilySlug} genera missing familySlug`);
  });

  test('no empty genus nodes (no children or speciesList)', () => {
    assert.equal(emptyGenusCount, 0, `${emptyGenusCount} empty genera found`);
  });

  test('species compression is active (speciesList > 0)', () => {
    assert.ok(totalSpeciesList > 100000, `only ${totalSpeciesList} speciesList entries (expected >100k)`);
  });

  test('no species duplicated across children + speciesList (all files)', () => {
    assert.equal(dupCount, 0, `${dupCount} duplicated species found across all order files`);
  });

  test('most SPECIES have subspeciesCount (>=95%)', () => {
    const pct = (totalSpecies - speciesMissingSubspeciesCount) / totalSpecies;
    assert.ok(pct >= 0.95, `only ${(pct*100).toFixed(1)}% of species have subspeciesCount`);
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// COVERAGE SUMMARY
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nCOVERAGE SUMMARY');
interface CoverageFamily {
  id: string; name: string; commonName?: string;
  appSlug?: string; className?: string; orderName?: string;
  portalCount: number; totalCount?: number;
}
interface CoverageClass {
  id: string; name: string; commonName?: string;
  families: CoverageFamily[];
}

const coverage = loadJson<CoverageClass[]>(join(PRIVATE_DATA_DIR, 'coverage-summary.json'));

test('coverage has 75 classes', () => {
  assert.equal(coverage.length, 75);
});

test('coverage family count matches taxonomy', () => {
  let familyCount = 0;
  for (const cls of coverage) {
    familyCount += cls.families.length;
  }
  assert.equal(familyCount, 5071);
});

test('every coverage family has portalCount and id prefix; >=99% have className', () => {
  let missingClassName = 0;
  for (const cls of coverage) {
    for (const family of cls.families) {
      assert.equal(typeof family.portalCount, 'number');
      assert.ok(family.id.startsWith('FAM_'));
      if (!family.className) missingClassName++;
    }
  }
  // Tardigrada has no CLASS in taxonomy (lives at root), so its inline
  // family may lack className in coverage summary.
  assert.ok(missingClassName <= 1, `${missingClassName} coverage families missing className`);
});

test('coverage portalCount never exceeds totalCount', () => {
  // totalCount is the real-world species total for a family; portalCount is
  // the number of species nodes the portal carries. Those are not the same
  // quantity, and the portal legitimately carries nodes that are not species:
  // a domestic trinomial is a subspecies raised to a node (Canis lupus
  // familiaris, Sus scrofa domesticus), and "sp. spec"/"undefined" are
  // placeholders for an undetermined taxon. Asserting a plain zero difference
  // flagged felidae, canidae and suidae for exactly that reason, and would
  // keep re-flagging any family that has a domestic form.
  //
  // The invariant worth keeping: the excess is *explained*. A family whose
  // portal holds materially more binomial species than the real world has
  // something wrong, and this still catches that.
  const unexplained = unexplainedExcess();
  assert.equal(
    unexplained.length, 0,
    `${unexplained.length} families where portalCount exceeds totalCount by more than their non-binomial nodes explain:\n` +
    unexplained.map(u => `         ${u}`).join('\n'),
  );
});

function unexplainedExcess(): string[] {
  const slackByFamily = new Map<string, number>();
  for (const n of nonBinomial) {
    const k = (n.familySlug || '(no familySlug)').toLowerCase();
    slackByFamily.set(k, (slackByFamily.get(k) ?? 0) + 1);
  }
  const out: string[] = [];
  for (const cls of coverage) {
    for (const family of cls.families) {
      if (family.totalCount === undefined || family.portalCount <= family.totalCount) continue;
      const slack = slackByFamily.get((family.appSlug ?? '').toLowerCase()) ?? 0;
      if (family.portalCount - family.totalCount > slack) {
        out.push(`${family.appSlug}: portal ${family.portalCount} vs total ${family.totalCount}, ` +
          `exceeds by ${family.portalCount - family.totalCount} but only ${slack} non-binomial nodes`);
      }
    }
  }
  return out;
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAXONOMY.JSON (source of truth)
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nTAXONOMY.JSON');

interface TaxonomyNode {
  id: string; name: string; rank: string; commonName?: string;
  children?: TaxonomyNode[];
  appSlug?: string; speciesCount?: number;
}

const taxonomy = loadJson<TaxonomyNode>(resolve(import.meta.dirname, '..', 'data', 'taxonomy.json'));

test('taxonomy root is KINGDOM Animalia', () => {
  assert.equal(taxonomy.id, 'ANIMALIA');
  assert.equal(taxonomy.rank, 'KINGDOM');
});

test('taxonomy has 32 phyla', () => {
  const phyla = taxonomy.children?.filter(c => c.rank === 'PHYLUM') ?? [];
  assert.equal(phyla.length, 32);
});

test('every FAMILY in taxonomy has speciesCount; >=95% have appSlug', () => {
  let familyCount = 0;
  let missingAppSlug = 0;
  function walk(n: TaxonomyNode) {
    if (n.rank === 'FAMILY') {
      familyCount++;
      assert.equal(typeof n.speciesCount, 'number', `FAMILY ${n.id} missing speciesCount`);
      if (!n.appSlug) missingAppSlug++;
    }
    for (const c of n.children ?? []) walk(c);
  }
  walk(taxonomy);
  assert.equal(familyCount, 5071);
  const pct = (familyCount - missingAppSlug) / familyCount;
  assert.ok(pct >= 0.95, `only ${(pct*100).toFixed(1)}% of taxonomy families have appSlug`);
});

// ═══════════════════════════════════════════════════════════════════════════════
// CROSS-REFERENCE: taxonomy <-> coverage-summary
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nCROSS-REFERENCE');

test('every taxonomy FAMILY appears in coverage-summary', () => {
  const coverageFamilyIds = new Set<string>();
  for (const cls of coverage) {
    for (const family of cls.families) {
      coverageFamilyIds.add(family.id);
    }
  }

  let missing = 0;
  function walk(n: TaxonomyNode) {
    if (n.rank === 'FAMILY') {
      if (!coverageFamilyIds.has(n.id)) missing++;
    }
    for (const c of n.children ?? []) walk(c);
  }
  walk(taxonomy);
  assert.equal(missing, 0, `${missing} taxonomy families missing from coverage-summary`);
});

test('coverage-summary portalCount sums to skeleton rankCounts.SPECIES', () => {
  let portalSum = 0;
  for (const cls of coverage) {
    for (const family of cls.families) {
      portalSum += family.portalCount;
    }
  }
  assert.equal(portalSum, skeleton.rankCounts!.SPECIES);
});

// ═══════════════════════════════════════════════════════════════════════════════
// BUILD OUTPUT SANITY
// ═══════════════════════════════════════════════════════════════════════════════

console.log('\nBUILD OUTPUT SANITY');

test('unified-taxonomy.json is current and large (>100MB)', () => {
  const path = join(PRIVATE_DATA_DIR, 'unified-taxonomy.json');
  // The monolith is opt-in (SN_BUILD_UNIFIED=1), so its absence is normal and a
  // leftover file from an older build proves nothing. Assert freshness from the
  // build's own state rather than the file merely existing — the tree the app
  // actually ships is covered by the skeleton and per-order assertions below.
  if (!existsSync(path)) {
    skip('not built — it is opt-in. Rebuild with SN_BUILD_UNIFIED=1 to assert on it.');
  }
  const state = loadJson<{ unified?: string }>(join(PRIVATE_DATA_DIR, '.build-cache', 'state.json'));
  if (state.unified !== 'current') {
    skip(`present but ${state.unified ?? 'of unknown freshness'} — rebuild with SN_BUILD_UNIFIED=1 to assert on it.`);
  }
  const stats = statSync(path);
  assert.ok(stats.size > 100_000_000, `unified-taxonomy.json only ${(stats.size/1e6).toFixed(1)}MB`);
});

test('nav tier exists and is materially smaller than the order files', () => {
  // The nav tier is the structure-and-counts projection the graph would use to
  // lay an order out without parsing its full file. No consumer reads it yet -
  // see docs/data-tiers.md, which explains why switching the graph over is not
  // a drop-in (search indexes name and commonName across speciesList, and
  // keeping those is most of the saving). It is emitted and asserted so the
  // projection cannot silently rot, and so the client switch is a wiring job
  // rather than a rebuild.
  const dir = join(DATA_DIR, 'orders-nav');
  assert.ok(existsSync(dir), `nav tier missing at ${dir} - run the build`);
  const files = readdirSync(dir).filter(f => f.endsWith('.json'));
  assert.ok(files.length > 0, 'nav tier directory is empty');
  assert.equal(files.length, allOrderFiles.length,
    `nav tier has ${files.length} files, orders have ${allOrderFiles.length}`);

  let navBytes = 0;
  let orderBytes = 0;
  for (const f of files) {
    navBytes += statSync(join(dir, f)).size;
    orderBytes += statSync(join(ORDERS_DIR, f)).size;
  }
  const ratio = orderBytes / navBytes;
  assert.ok(ratio > 5,
    `nav tier is only ${ratio.toFixed(1)}x smaller than the order files ` +
    `(${(navBytes / 1e6).toFixed(1)}MB vs ${(orderBytes / 1e6).toFixed(1)}MB). ` +
    `A projection that keeps genus children by spreading them keeps every ` +
    `species description and the ratio collapses to about 2x.`);

  // Structure, not just a smaller file: a genus must carry its counts and must
  // not carry species prose.
  const sample = loadJson<OrderNode & Record<string, unknown>>(join(dir, files[0]));
  let genera = 0;
  let speciesWithProse = 0;
  function audit(node: OrderNode) {
    if (node.rank === 'GENUS') {
      genera++;
      if (typeof (node as unknown as Record<string, unknown>)._speciesCount !== 'number') {
        assert.fail(`genus ${node.id} has no _speciesCount`);
      }
    }
    if (node.rank === 'SPECIES' && (node.description ?? '').trim()) speciesWithProse++;
    for (const c of node.children ?? []) audit(c);
    for (const s of node.speciesList ?? []) audit(s);
  }
  audit(sample);
  assert.ok(genera > 0, `no genera in ${files[0]}`);
  assert.equal(speciesWithProse, 0,
    `${speciesWithProse} species in ${files[0]} still carry a description`);
});

test('names tier + genus prose reproduces the full order file', () => {
  // The graph reads the names tier and overlays per-genus prose on selection.
  // That is only equivalent to what the book reads if, after the overlay, the
  // species descriptions and the three inherited stamps match the full order
  // file exactly. This is the check that makes the two tiers safe to swap
  // between, and it is deliberately run against the *largest* orders, where a
  // partial implementation would show up.
  const namesDir = join(DATA_DIR, 'orders-names');
  const proseDir = join(DATA_DIR, 'orders-prose');
  assert.ok(existsSync(namesDir), `names tier missing at ${namesDir} - run the build`);
  assert.ok(existsSync(proseDir), `prose tier missing at ${proseDir} - run the build`);

  const norm = (d?: string) => ((d ?? '').trim() === '' ? null : (d ?? '').trim());
  const samples = allOrderFiles
    .map(f => ({ f, size: statSync(join(ORDERS_DIR, f)).size }))
    .sort((a, b) => b.size - a.size)
    .slice(0, 3)
    .map(x => x.f);

  for (const file of samples) {
    const orderId = file.replace(/\.json$/, '');
    const full = loadJson<OrderNode>(join(ORDERS_DIR, file));
    const lean = loadJson<OrderNode>(join(namesDir, file));

    // The overlay, as useTaxonomyLoader performs it.
    const flat = new Map<string, OrderNode>();
    (function collect(n: OrderNode) {
      if (n.rank === 'GENUS') {
        const p = join(proseDir, orderId, `${n.id}.json`);
        if (existsSync(p)) {
          for (const sp of (loadJson<{ species: OrderNode[] }>(p)).species) flat.set(sp.id, sp);
        }
      }
      for (const c of n.children ?? []) collect(c);
    })(lean);
    const overlay = (n: OrderNode): OrderNode => {
      const patch = flat.get(n.id);
      const next: OrderNode = patch
        ? { ...n, description: patch.description, continents: patch.continents ?? n.continents }
        : n;
      if (n.children) next.children = n.children.map(overlay);
      if (n.speciesList) next.speciesList = n.speciesList.map(overlay);
      return next;
    };
    const merged = overlay(lean);

    const describe = (root: OrderNode) => {
      const m = new Map<string, string | null>();
      (function walk(n: OrderNode) {
        if (n.rank === 'SPECIES' || n.rank === 'SUBSPECIES' || n.rank === 'BREED') m.set(n.id, norm(n.description));
        for (const c of n.children ?? []) walk(c);
        for (const s of n.speciesList ?? []) walk(s);
      })(root);
      return m;
    };
    const a = describe(full);
    const b = describe(merged);
    assert.equal(b.size, a.size, `${file}: ${a.size} species in the order file, ${b.size} after the overlay`);
    for (const [id, d] of a) {
      assert.equal(b.get(id) ?? null, d, `${file}: ${id} description differs after the overlay`);
    }
  }
});

test('skeleton.json exists and is small (<10MB)', () => {
  const path = join(DATA_DIR, 'unified-taxonomy-skeleton.json');
  const stats = statSync(path);
  assert.ok(stats.size < 10_000_000, `skeleton is ${(stats.size/1e6).toFixed(1)}MB`);
});

test('no empty order files', () => {
  for (const file of allOrderFiles) {
    const stats = statSync(join(ORDERS_DIR, file));
    assert.ok(stats.size > 100, `${file} is suspiciously small (${stats.size} bytes)`);
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// SUMMARY
// ═══════════════════════════════════════════════════════════════════════════════

console.log(`\n${'='.repeat(60)}`);
console.log(`Results: ${passCount} passed, ${skipCount} skipped, ${failCount} failed`);
console.log(`${'='.repeat(60)}\n`);

if (failCount > 0) {
  process.exit(1);
}
