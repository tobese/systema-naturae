import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import type { TaxonNode } from "@shared/types";
import { annotatePortalLevels } from "../colors";

export interface OrderInfo {
  orderId: string;
  classSlug: string;
  orderSlug: string;
  file: string;
  /** Structure and names, species prose removed. What the graph loads. */
  namesFile: string;
  /** Per-genus species descriptions, fetched when a genus is opened. */
  proseDir: string;
  familyCount: number;
  speciesCount: number;
  familySlugs: string[];
}

export interface Manifest {
  orders: Record<string, OrderInfo>;
  familyToOrder: Record<string, string>;
}

const MAX_CACHED_ORDERS = 3;

function mergeOrders(
  node: TaxonNode,
  cache: Map<string, TaxonNode>,
): TaxonNode {
  if (node.rank === "ORDER" && cache.has(node.id)) {
    return cache.get(node.id)!;
  }
  if (!node.children) return node;
  return {
    ...node,
    children: node.children.map(c => mergeOrders(c, cache)),
  };
}

/** Nearest GENUS ancestor of `nodeId` within a loaded order subtree. */
function findGenusId(order: TaxonNode | undefined, nodeId: string): string | undefined {
  if (!order) return undefined;
  let found: string | undefined;
  const walk = (n: TaxonNode): boolean => {
    if (n.id === nodeId) { found = n.rank === "GENUS" ? n.id : undefined; return true; }
    if (n.rank === "GENUS" && n.children?.some(c => { if (walk(c)) { found = found ?? n.id; return true; } return false; })) return true;
    for (const c of n.children ?? []) if (walk(c)) return true;
    for (const s of n.speciesList ?? []) if (walk(s)) return true;
    return false;
  };
  walk(order);
  return found;
}

/** Overlay loaded species prose onto a tree. `prose` is keyed by species id. */
function applyProse(node: TaxonNode, prose: Map<string, TaxonNode>): TaxonNode {
  const patch = prose.get(node.id);
  const next: TaxonNode = patch
    ? {
        ...node,
        description: patch.description,
        continents: patch.continents ?? node.continents,
        subspeciesCount: patch.subspeciesCount ?? node.subspeciesCount,
      }
    : node;
  if (node.children) next.children = node.children.map(c => applyProse(c, prose));
  if (node.speciesList) next.speciesList = node.speciesList.map(s => applyProse(s, prose));
  return next;
}

function touchLRU(arr: string[], id: string): void {
  const idx = arr.indexOf(id);
  if (idx !== -1) arr.splice(idx, 1);
  arr.push(id);
}

/**
 * Re-derive the stamps the names tier dropped.
 *
 * `className`, `orderName`, `familySlug` and `lineage` are constant for the
 * family or genus a species sits under, and repeated on all 527,630 animalia
 * species they are ~16MB of every large order file. buildData drops them from
 * `orders-names/`; this puts them back by walking down.
 *
 * Only *missing* fields are filled, so running this over a full order file is a
 * no-op and the book is unaffected.
 *
 * `lineage` is not derived: it is usually the genus but 379 animalia nodes have
 * none, and filling those would invent a value the source does not have. It
 * stays in the tier - 7% of the bytes for a change that is then provably
 * behaviour-neutral, which is the trade worth making.
 *
 * `rank` is not inferred either. It is read 79 times across the graph and
 * position is a poor substitute.
 */
function inheritStamps(node: TaxonNode, ctx: {
  className?: string; orderName?: string; familySlug?: string;
} = {}): TaxonNode {
  const nextClass = node.className ?? (node.rank === "CLASS" ? node.name : ctx.className);
  const nextOrder = node.orderName ?? (node.rank === "ORDER" ? node.name : ctx.orderName);
  // FAMILY nodes already carry familySlug from the build, so this only has to
  // pass it down - there is no appSlug on a tree node to fall back to.
  const nextFamily = node.familySlug ?? ctx.familySlug;
  const out: TaxonNode = { ...node };
  if (out.className === undefined) out.className = nextClass;
  if (out.orderName === undefined) out.orderName = nextOrder;
  if (out.familySlug === undefined) out.familySlug = nextFamily;

  if (node.children) {
    out.children = node.children.map(c =>
      inheritStamps(c, { className: nextClass, orderName: nextOrder, familySlug: nextFamily }),
    );
  }
  if (node.speciesList) {
    out.speciesList = node.speciesList.map(s =>
      inheritStamps(s, { className: nextClass, orderName: nextOrder, familySlug: nextFamily }),
    );
  }
  return out;
}

export function useTaxonomyLoader(kingdom = "animalia"): {
  taxonomyData: TaxonNode | null;
  loading: boolean;
  manifest: Manifest | null;
  loadOrder: (orderId: string) => void;
  /** Fetch species prose for the genus containing `nodeId`. */
  loadProseFor: (orderId: string, nodeId: string) => void;
  isOrderLoading: (orderId: string) => boolean;
  loadedOrders: Set<string>;
} {
  const [skeleton, setSkeleton] = useState<TaxonNode | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [cacheVersion, setCacheVersion] = useState(0);
  const [inflightOrders, setInflightOrders] = useState<Set<string>>(new Set());
  const orderCache = useRef<Map<string, TaxonNode>>(new Map());
  const accessOrder = useRef<string[]>([]);
  // genusId -> (speciesId -> record from orders-prose). Held beside the order
  // cache rather than inside it, so replacing an order does not throw away
  // prose that is still valid for the genera underneath it.
  const proseCache = useRef<Map<string, Map<string, TaxonNode>>>(new Map());
  const proseInflight = useRef<Set<string>>(new Set());
  const [proseVersion, setProseVersion] = useState(0);

  const base = import.meta.env.BASE_URL ?? "/";

  useEffect(() => {
    Promise.all([
      fetch(`${base}data/kingdoms/${kingdom}/unified-taxonomy-skeleton.json`).then(r => r.json()),
      fetch(`${base}data/kingdoms/${kingdom}/order-manifest.json`).then(r => r.json()),
    ])
      .then(([sk, mf]) => {
        setSkeleton(annotatePortalLevels(sk as TaxonNode));
        setManifest(mf as Manifest);
        setLoading(false);
      })
      .catch(e => {
        console.error("Failed to load taxonomy:", e);
        setLoading(false);
      });
  }, [kingdom, base]);

  const loadOrder = useCallback((orderId: string) => {
    if (orderCache.current.has(orderId)) {
      touchLRU(accessOrder.current, orderId);
      setCacheVersion(v => v + 1);
      return;
    }

    setInflightOrders(prev => new Set(prev).add(orderId));

    const orderPath = manifest?.orders[orderId]?.namesFile;
    if (!orderPath) {
      console.error(`Order ${orderId} not found in manifest`);
      setInflightOrders(prev => {
        const next = new Set(prev);
        next.delete(orderId);
        return next;
      });
      return;
    }

    fetch(`${base}${orderPath}`)
      .then(r => r.json())
      .then((raw: TaxonNode) => {
        // The names tier omits the inherited stamps; put them back before the
        // tree is annotated, so colours, lineage and search all see the same
        // values the full order file carried.
        const annotated = annotatePortalLevels(inheritStamps(raw));

        if (orderCache.current.size >= MAX_CACHED_ORDERS && accessOrder.current.length > 0) {
          const oldest = accessOrder.current.shift()!;
          orderCache.current.delete(oldest);
        }

        orderCache.current.set(orderId, annotated);
        touchLRU(accessOrder.current, orderId);
        setCacheVersion(v => v + 1);
        setInflightOrders(prev => {
          const next = new Set(prev);
          next.delete(orderId);
          return next;
        });
      })
      .catch(e => {
        console.error(`Failed to load order ${orderId}:`, e);
        setInflightOrders(prev => {
          const next = new Set(prev);
          next.delete(orderId);
          return next;
        });
      });
  }, [manifest, base]);

  /**
   * Fetch the species descriptions for the genus containing `nodeId`.
   *
   * The names tier carries no species prose, so without this every species
   * panel renders empty - the graph would look as though it had lost its
   * descriptions rather than as though it had not loaded them yet. One file
   * per genus: 3KB median, 1.23MB worst case, against 43MB for the order.
   */
  const loadProseFor = useCallback((orderId: string, nodeId: string) => {
    const genusId = findGenusId(orderCache.current.get(orderId), nodeId);
    if (!genusId) return;
    const key = `${orderId}/${genusId}`;
    if (proseCache.current.has(genusId) || proseInflight.current.has(key)) return;
    const dir = manifest?.orders[orderId]?.proseDir;
    if (!dir) return;
    proseInflight.current.add(key);
    fetch(`${base}${dir}/${genusId}.json`)
      .then(r => (r.ok ? r.json() : { species: [] }))
      .then((payload: { genus: string; species: TaxonNode[] }) => {
        const byId = new Map<string, TaxonNode>();
        for (const sp of payload.species ?? []) byId.set(sp.id, sp);
        proseCache.current.set(genusId, byId);
        setProseVersion(v => v + 1);
      })
      .catch(() => {
        // No prose file for a genus is normal - only 38% of genera have any.
        // Record the empty result so it is not refetched on every selection.
        proseCache.current.set(genusId, new Map());
      })
      .finally(() => { proseInflight.current.delete(key); });
  }, [manifest, base]);

  // One flat speciesId -> record map, so the overlay is a lookup per node
  // rather than a scan of the loaded genera.
  const flattenedProse = useMemo(() => {
    void proseVersion;
    const flat = new Map<string, TaxonNode>();
    for (const byId of proseCache.current.values()) {
      for (const [id, rec] of byId) flat.set(id, rec);
    }
    return flat;
  }, [proseVersion]);

  const taxonomyData = useMemo(() => {
    if (!skeleton) return null;
    const merged = orderCache.current.size === 0 ? skeleton : mergeOrders(skeleton, orderCache.current);
    return flattenedProse.size === 0 ? merged : applyProse(merged, flattenedProse);
  }, [skeleton, cacheVersion, proseVersion, flattenedProse]);

  const isOrderLoading = useCallback(
    (orderId: string) => inflightOrders.has(orderId),
    [inflightOrders],
  );

  const loadedOrders = useMemo(() => new Set(orderCache.current.keys()), [cacheVersion]);

  return {
    taxonomyData,
    loading,
    manifest,
    loadOrder,
    loadProseFor,
    isOrderLoading,
    loadedOrders,
  };
}
