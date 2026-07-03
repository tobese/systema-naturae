import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import type { TaxonNode } from "@shared/types";
import { annotatePortalLevels } from "../colors";

export interface OrderInfo {
  orderId: string;
  classSlug: string;
  orderSlug: string;
  file: string;
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

function touchLRU(arr: string[], id: string): void {
  const idx = arr.indexOf(id);
  if (idx !== -1) arr.splice(idx, 1);
  arr.push(id);
}

export function useTaxonomyLoader(): {
  taxonomyData: TaxonNode | null;
  loading: boolean;
  manifest: Manifest | null;
  loadOrder: (orderId: string) => void;
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

  const base = import.meta.env.BASE_URL ?? "/";

  useEffect(() => {
    Promise.all([
      fetch(`${base}data/unified-taxonomy-skeleton.json`).then(r => r.json()),
      fetch(`${base}data/order-manifest.json`).then(r => r.json()),
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
  }, []);

  const loadOrder = useCallback((orderId: string) => {
    if (orderCache.current.has(orderId)) {
      touchLRU(accessOrder.current, orderId);
      setCacheVersion(v => v + 1);
      return;
    }

    setInflightOrders(prev => new Set(prev).add(orderId));

    fetch(`${base}data/orders/${orderId}.json`)
      .then(r => r.json())
      .then((raw: TaxonNode) => {
        const annotated = annotatePortalLevels(raw);

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
  }, []);

  const taxonomyData = useMemo(() => {
    if (!skeleton) return null;
    if (orderCache.current.size === 0) return skeleton;
    return mergeOrders(skeleton, orderCache.current);
  }, [skeleton, cacheVersion]);

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
    isOrderLoading,
    loadedOrders,
  };
}
