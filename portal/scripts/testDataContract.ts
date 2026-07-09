import { readFileSync, readdirSync, statSync } from 'fs';
import { resolve, join } from 'path';
import { strict as assert } from 'assert';

const KINGDOM = 'animalia';
const DATA_DIR = resolve(import.meta.dirname, '..', 'data', 'kingdoms', KINGDOM);
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

let passCount = 0;
let failCount = 0;

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`  PASS  ${name}`);
    passCount++;
  } catch (err) {
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
  assert.equal(rc.GENUS, 57348);
  assert.equal(rc.SPECIES, 529298);
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
  const baseDir = resolve(import.meta.dirname, '..');
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
    FAMILY: 5071, GENUS: 57348, SPECIES: 529298,
    SUBFAMILY: 8, TRIBE: 10, SUBSPECIES: 851,
    BREED_GROUP: 25, BREED: 115, HYBRID_GROUP: 1, HYBRID: 4,
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
    familyCount: 5, speciesCount: 1013,
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

const coverage = loadJson<CoverageClass[]>(join(DATA_DIR, 'coverage-summary.json'));

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
  let violations = 0;
  for (const cls of coverage) {
    for (const family of cls.families) {
      if (family.totalCount !== undefined && family.portalCount > family.totalCount) {
        violations++;
      }
    }
  }
  assert.equal(violations, 0, `${violations} families where portalCount > totalCount`);
});

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

test('unified-taxonomy.json exists and is large (>100MB)', () => {
  const path = join(DATA_DIR, 'unified-taxonomy.json');
  const stats = statSync(path);
  assert.ok(stats.size > 100_000_000, `unified-taxonomy.json only ${(stats.size/1e6).toFixed(1)}MB`);
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
console.log(`Results: ${passCount} passed, ${failCount} failed`);
console.log(`${'='.repeat(60)}\n`);

if (failCount > 0) {
  process.exit(1);
}
