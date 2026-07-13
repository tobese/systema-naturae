/**
 * AppBare — bare-bones portal: graph + side panels only.
 *
 * A stripped-down twin of App.tsx (no header, search, bell, options, modals,
 * wheel, book, habitat map). Reuses the same data hooks and selection logic.
 * Intended as the minimal shell (e.g. for the in-development plant mirror).
 * Entry: bare.html → main-bare.tsx.
 */
import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import FamilyTree from "@shared/components/FamilyTree";
import NodeNav from "@shared/components/NodeNav";
import type { TaxonNode } from "@shared/types";
import { useUnifiedTree } from "./hooks/useUnifiedTree";
import { useUrlState } from "./hooks/useUrlState";
import { useTaxonomyLoader } from "./hooks/useTaxonomyLoader";
import UnifiedInfoPanel from "./components/UnifiedInfoPanel";
import TaxonomySidebar from "./components/TaxonomySidebar";
import { ColorRegistryContext } from "./components/ColorRegistryContext.tsx";

const OPTIONS = { showExtinct: true, showFossil: true, collapseThreshold: 30, nodeScale: 1.0, highlightWikipedia: false, highlightFossilExtinct: false };

function filterExtinct(node: TaxonNode | null): TaxonNode {
  if (!node) return { id: "", name: "", rank: "PHYLUM", children: [] } as unknown as TaxonNode;
  if (!node.children) return node;
  const filtered = node.children.filter(c => !c.extinct).map(c => filterExtinct(c));
  return { ...node, children: filtered.length > 0 ? filtered : undefined };
}

function filterFossil(node: TaxonNode | null): TaxonNode {
  if (!node) return { id: "", name: "", rank: "PHYLUM", children: [] } as unknown as TaxonNode;
  if (!node.children) return node;
  const filtered = node.children.filter(c => !c.fossil).map(c => filterFossil(c));
  return { ...node, children: filtered.length > 0 ? filtered : undefined };
}

function walkFind(node: TaxonNode, id: string): TaxonNode | null {
  if (node.id === id) return node;
  if (node.speciesList) {
    const foundSp = node.speciesList.find(s => s.id === id);
    if (foundSp) return foundSp;
  }
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
}

function getPathToNode(root: TaxonNode, targetId: string): TaxonNode[] {
  function walk(node: TaxonNode, path: TaxonNode[]): TaxonNode[] | null {
    const next = [...path, node];
    if (node.id === targetId) return next;
    if (node.speciesList) {
      const foundSp = node.speciesList.find(s => s.id === targetId);
      if (foundSp) return [...next, foundSp];
    }
    for (const child of node.children ?? []) {
      const found = walk(child, next);
      if (found) return found;
    }
    return null;
  }
  return walk(root, []) ?? [];
}

function findNavContext(tree: TaxonNode, targetId: string): { parent: TaxonNode | null; siblings: TaxonNode[]; index: number } {
  if (tree.id === targetId) return { parent: null, siblings: [], index: 0 };
  function walk(node: TaxonNode): { parent: TaxonNode; siblings: TaxonNode[]; index: number } | null {
    const children = node.children ?? [];
    const idx = children.findIndex(c => c.id === targetId);
    if (idx !== -1) return { parent: node, siblings: children, index: idx };
    if (node.speciesList) {
      const spIdx = node.speciesList.findIndex(s => s.id === targetId);
      if (spIdx !== -1) {
        const allSiblings = [...children, ...node.speciesList];
        return { parent: node, siblings: allSiblings, index: children.length + spIdx };
      }
    }
    for (const child of children) { const found = walk(child); if (found) return found; }
    return null;
  }
  return walk(tree) ?? { parent: null, siblings: [], index: 0 };
}

import type { ColorTheme } from "@shared/types";

interface AppBareProps {
  kingdom?: string;
  colorRegistry: Record<string, ColorTheme>;
}

export default function AppBare({ kingdom = "animalia", colorRegistry }: AppBareProps) {
  const [layout, setLayout] = useState<"radial" | "vertical">("radial");
  const [showSidebar, setShowSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(false);
  const [expandedSubspeciesIds, setExpandedSubspeciesIds] = useState<Set<string>>(new Set());
  const [expandedBreedIds, setExpandedBreedIds] = useState<Set<string>>(new Set());
  const [treeRotation, setTreeRotation] = useState(0);
  const [tooltipTargetId, setTooltipTargetId] = useState<string | null>(null);
  const pendingZoomId = useRef<string | null>(null);
  const sidebarScrollRef = useRef<HTMLDivElement>(null);

  const { taxonomyData, loading, manifest, loadOrder, loadedOrders } = useTaxonomyLoader(kingdom);
  const { focusedFamilySlug, focusedClassId, focusedOrderId, selectedNodeId, setFocus, setFocusedClass, setSelectedNodeId, navigateTo } = useUrlState();

  const showSplash = loading || !taxonomyData;

  const selected = useMemo(
    () => (selectedNodeId && taxonomyData ? walkFind(taxonomyData, selectedNodeId) : null),
    [selectedNodeId, taxonomyData],
  );

  useEffect(() => { if (selected) setShowRightSidebar(true); }, [selected]);
  useEffect(() => { sidebarScrollRef.current?.scrollTo({ top: 0, behavior: "instant" }); }, [selectedNodeId]);
  useEffect(() => {
    if (!tooltipTargetId) return;
    const t = setTimeout(() => setTooltipTargetId(null), 2000);
    return () => clearTimeout(t);
  }, [tooltipTargetId]);

  const focusedFamilyId = useMemo(() => {
    if (!focusedFamilySlug || !taxonomyData) return null;
    function find(n: TaxonNode): string | null {
      if (n.rank === "FAMILY" && n.familySlug === focusedFamilySlug) return n.id;
      for (const c of n.children ?? []) { const r = find(c); if (r) return r; }
      return null;
    }
    return find(taxonomyData);
  }, [focusedFamilySlug, taxonomyData]);

  const lastAutoZoomFamilyId = useRef<string | null>(null);
  useEffect(() => {
    if (!focusedFamilyId) { lastAutoZoomFamilyId.current = null; return; }
    if (pendingZoomId.current) return;
    if (lastAutoZoomFamilyId.current === focusedFamilyId) return;
    pendingZoomId.current = focusedFamilyId;
    lastAutoZoomFamilyId.current = focusedFamilyId;
  }, [focusedFamilyId]);

  const { treeData, colorTheme, highlightedNodeIds, findNodeById } = useUnifiedTree(
    taxonomyData, focusedFamilyId, focusedClassId, expandedSubspeciesIds, expandedBreedIds, null, false, false, loadedOrders, colorRegistry,
  );

  const deepLinkedOrders = useRef<Set<string>>(new Set());
  useEffect(() => {
    if (!manifest || loading) return;
    let orderId: string | null = null;
    if (focusedOrderId && manifest.orders[focusedOrderId]) orderId = focusedOrderId;
    else if (focusedFamilySlug) orderId = manifest.familyToOrder[focusedFamilySlug] ?? null;
    if (orderId && !deepLinkedOrders.current.has(orderId)) {
      deepLinkedOrders.current.add(orderId);
      loadOrder(orderId);
    }
  }, [focusedFamilySlug, focusedOrderId, manifest, loading, loadOrder]);

  const filteredTreeData = useMemo(() => {
    let data = treeData;
    if (!OPTIONS.showExtinct) data = filterExtinct(data);
    if (!OPTIONS.showFossil) data = filterFossil(data);
    return data;
  }, [treeData]);

  const handleSelect = useCallback((node: TaxonNode | null) => {
    if (!node) { setSelectedNodeId(null); return; }
    if (node.rank === "KINGDOM" || node.rank === "PHYLUM") {
      setFocusedClass(null, node.id); pendingZoomId.current = node.id; return;
    }
    if (node.rank === "CLASS") {
      if (node.id === focusedClassId) { setFocusedClass(null, null); pendingZoomId.current = node.id; }
      else { setFocusedClass(node.id, node.id); pendingZoomId.current = node.id; }
      return;
    }
    if (node.rank === "FAMILY") {
      const slug = node.familySlug ?? null;
      if (slug === focusedFamilySlug) {
        setFocus(null); setExpandedSubspeciesIds(new Set()); setExpandedBreedIds(new Set());
      } else {
        navigateTo(slug, node.id); setExpandedSubspeciesIds(new Set()); setExpandedBreedIds(new Set());
        pendingZoomId.current = node.id;
      }
      return;
    }
    if (focusedFamilySlug && node.familySlug !== focusedFamilySlug) {
      setExpandedSubspeciesIds(new Set()); setExpandedBreedIds(new Set());
      navigateTo(node.familySlug ?? null, node.id);
      if (node.familySlug) pendingZoomId.current = node.id;
      return;
    }
    if (node.rank === "SPECIES") {
      const fullNode = taxonomyData ? walkFind(taxonomyData, node.id) : null;
      const hasSubspecies = fullNode?.children?.some(c => c.rank === "SUBSPECIES") ?? false;
      const hasBreeds = fullNode?.children?.some(c => c.rank === "BREED_GROUP") ?? false;
      if (hasSubspecies) {
        setExpandedSubspeciesIds(prev => { const next = new Set(prev); if (next.has(node.id)) next.delete(node.id); else { next.add(node.id); pendingZoomId.current = node.id; } return next; });
      } else if (hasBreeds) {
        setExpandedBreedIds(prev => { const next = new Set(prev); if (next.has(node.id)) next.delete(node.id); else { next.add(node.id); pendingZoomId.current = node.id; } return next; });
      }
    }
    if (node.rank === "ORDER" && node._dataFile && !loadedOrders.has(node.id)) loadOrder(node.id);
    const ZOOM_RANKS = new Set(["ORDER", "SUBFAMILY", "TRIBE", "GENUS", "BREED_GROUP", "HYBRID_GROUP"]);
    if (ZOOM_RANKS.has(node.rank)) pendingZoomId.current = node.id;
    setSelectedNodeId(selectedNodeId === node.id ? null : node.id);
  }, [focusedFamilySlug, focusedClassId, selectedNodeId, setFocus, setFocusedClass, setSelectedNodeId, navigateTo, taxonomyData, loadedOrders, loadOrder]);

  const handleCollapseFamily = useCallback(() => {
    if (focusedFamilyId) pendingZoomId.current = focusedFamilyId;
    setFocus(null); setExpandedSubspeciesIds(new Set()); setExpandedBreedIds(new Set());
  }, [setFocus, focusedFamilyId]);
  const handleCollapseClass = useCallback(() => setFocusedClass(null, null), [setFocusedClass]);

  const selectedInTree = useMemo(() => selected ? (walkFind(treeData, selected.id) ?? selected) : null, [selected, treeData]);
  const navContext = useMemo(() => selected ? findNavContext(treeData, selected.id) : null, [selected, treeData]);
  const breadcrumbPath = useMemo(() => selected && taxonomyData ? getPathToNode(taxonomyData, selected.id) : [], [selected, taxonomyData]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "A") return;
      if (e.key === "Escape" && focusedFamilySlug) { handleCollapseFamily(); return; }
      if (e.key === "Escape" && focusedClassId) { handleCollapseClass(); return; }
      if ((e.key === "q" || e.key === "Q") && layout === "radial") { e.preventDefault(); setTreeRotation(r => r - 15); return; }
      if ((e.key === "e" || e.key === "E") && layout === "radial") { e.preventDefault(); setTreeRotation(r => r + 15); return; }
      if (!selected || !navContext) return;
      const { parent, siblings, index } = navContext;
      let nextNode: TaxonNode | null = null;
      if (e.key === "ArrowLeft" && siblings.length > 1) nextNode = siblings[(index - 1 + siblings.length) % siblings.length];
      else if (e.key === "ArrowRight" && siblings.length > 1) nextNode = siblings[(index + 1) % siblings.length];
      else if (e.key === "ArrowUp" && parent) { e.preventDefault(); nextNode = parent; }
      if (nextNode) { handleSelect(nextNode); setTooltipTargetId(nextNode.id); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, navContext, handleSelect, focusedFamilySlug, handleCollapseFamily, focusedClassId, handleCollapseClass, layout]);

  return (
    <ColorRegistryContext.Provider value={colorRegistry}>
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f1117", color: "#e0e0e8" }}>
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
          {!showSplash && (
            <FamilyTree
              data={filteredTreeData}
              layout={layout}
              onSelect={handleSelect}
              selectedId={selected?.id ?? null}
              pendingZoomId={pendingZoomId}
              highlightedNodeIds={highlightedNodeIds}
              colorTheme={colorTheme}
              focusedFamilySlug={focusedFamilySlug}
              focusedClassId={focusedClassId}
              collapseThreshold={OPTIONS.collapseThreshold}
              nodeScale={OPTIONS.nodeScale}
              treeRotation={treeRotation}
              tooltipTargetId={tooltipTargetId}
              onReady={() => {}}
            />
          )}

          {showSidebar && !showSplash && (
            <div style={{ position: "absolute", top: 0, left: 0, bottom: 0, width: 220, background: "rgba(10,10,20,0.85)", borderRight: "1px solid #1e2030", overflow: "hidden", zIndex: 10 }}>
              <TaxonomySidebar
                data={taxonomyData}
                focusedClassId={focusedClassId}
                focusedFamilySlug={focusedFamilySlug}
                selectedId={selected?.id ?? null}
                onSelect={handleSelect}
                onFocusFamily={setFocus}
                onFocusClass={setFocusedClass}
              />
            </div>
          )}

          {!showSplash && (
            <>
              <button onClick={() => setShowSidebar(o => !o)} title="Taxonomy sidebar"
                style={{ position: "absolute", top: 12, left: 12, zIndex: 20, width: 36, height: 36, borderRadius: 6, border: "1px solid " + (showSidebar ? "#4a4d60" : "#2a2a3a"), background: showSidebar ? "#1e2030" : "rgba(15,17,23,0.7)", color: showSidebar ? "#e0e0e8" : "#777", cursor: "pointer", fontSize: 18 }}>☰</button>
              <button onClick={() => setShowRightSidebar(o => !o)} title="Details panel"
                style={{ position: "absolute", top: 12, right: 12, zIndex: 20, width: 36, height: 36, borderRadius: 6, border: "1px solid " + (showRightSidebar ? "#4a4d60" : "#2a2a3a"), background: showRightSidebar ? "#1e2030" : "rgba(15,17,23,0.7)", color: showRightSidebar ? "#e0e0e8" : "#777", cursor: "pointer", fontSize: 18 }}>☰</button>
              <div style={{ position: "absolute", bottom: 16, left: 16, display: "flex", gap: 4, background: "rgba(10,10,20,0.6)", borderRadius: 6, padding: 4 }}>
                {(["radial", "vertical"] as const).map(l => (
                  <button key={l} onClick={() => setLayout(l)}
                    style={{ border: "none", borderRadius: 4, padding: "4px 10px", fontSize: 11, cursor: "pointer", background: layout === l ? "#2a2a3a" : "transparent", color: layout === l ? "#e0e0e0" : "#555" }}>
                    {l === "radial" ? "⊕ Radial" : "⇒ Vertical"}
                  </button>
                ))}
              </div>
            </>
          )}

          {showSplash && (
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>Loading…</div>
          )}
        </div>

        {showRightSidebar && (
          <div style={{ width: 380, borderLeft: "1px solid #1e2030", display: "flex", flexDirection: "column", flexShrink: 0 }}>
            {selected && navContext && (
              <NodeNav
                parent={navContext.parent}
                siblings={navContext.siblings}
                index={navContext.index}
                onNavigate={handleSelect}
                breadcrumbPath={breadcrumbPath}
                colorTheme={colorTheme}
              />
            )}
            <div ref={sidebarScrollRef} style={{ flex: 1, overflowY: "auto" }}>
              <UnifiedInfoPanel
                node={selectedInTree}
                onSelect={handleSelect}
                findNodeById={findNodeById}
                onFocusFamily={slug => setFocus(slug)}
                focusedFamilySlug={focusedFamilySlug}
              />
            </div>
          </div>
        )}
      </div>
    </div>
    </ColorRegistryContext.Provider>
  );
}
