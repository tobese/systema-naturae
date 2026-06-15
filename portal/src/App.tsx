import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import FamilyTree from "@shared/components/FamilyTree";
import HabitatMap from "@shared/components/HabitatMap";
import NodeNav from "@shared/components/NodeNav";
import type { TaxonNode } from "@shared/types";
import { annotatePortalLevels } from "./colors";
import { useUnifiedTree } from "./hooks/useUnifiedTree";
import { useUrlState } from "./hooks/useUrlState";
import UnifiedInfoPanel from "./components/UnifiedInfoPanel";
import Breadcrumb from "./components/Breadcrumb";
import rawJson from "../data/unified-taxonomy.json";

const annotatedData = annotatePortalLevels(rawJson as TaxonNode);

function walkFind(node: TaxonNode, id: string): TaxonNode | null {
  if (node.id === id) return node;
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
    for (const child of node.children ?? []) {
      const found = walk(child, next);
      if (found) return found;
    }
    return null;
  }
  return walk(root, []) ?? [];
}

function findNavContext(
  tree: TaxonNode,
  targetId: string,
): { parent: TaxonNode | null; siblings: TaxonNode[]; index: number } {
  if (tree.id === targetId) return { parent: null, siblings: [], index: 0 };
  function walk(node: TaxonNode): { parent: TaxonNode; siblings: TaxonNode[]; index: number } | null {
    const children = node.children ?? [];
    const idx = children.findIndex(c => c.id === targetId);
    if (idx !== -1) return { parent: node, siblings: children, index: idx };
    for (const child of children) {
      const found = walk(child);
      if (found) return found;
    }
    return null;
  }
  return walk(tree) ?? { parent: null, siblings: [], index: 0 };
}

export default function App() {
  const [layout, setLayout] = useState<"radial" | "vertical">("radial");
  const [expandedSubspeciesIds, setExpandedSubspeciesIds] = useState<Set<string>>(new Set());
  const [expandedBreedIds, setExpandedBreedIds] = useState<Set<string>>(new Set());
  const [highlightedContinent, setHighlightedContinent] = useState<string | null>(null);
  const pendingZoomId = useRef<string | null>(null);

  const { focusedFamilySlug, selectedNodeId, setFocus, setSelectedNodeId } = useUrlState();

  // selected node is fully URL-driven so browser back/forward and deep-links work correctly
  const selected = useMemo(
    () => (selectedNodeId ? walkFind(annotatedData, selectedNodeId) : null),
    [selectedNodeId],
  );

  // Resolve focused family slug → node id
  const focusedFamilyId = useMemo(() => {
    if (!focusedFamilySlug) return null;
    function find(n: TaxonNode): string | null {
      if (n.rank === "FAMILY" && n.familySlug === focusedFamilySlug) return n.id;
      for (const c of n.children ?? []) { const r = find(c); if (r) return r; }
      return null;
    }
    return find(annotatedData);
  }, [focusedFamilySlug]);

  const { treeData, colorTheme, highlightedNodeIds, findNodeById } = useUnifiedTree(
    annotatedData,
    focusedFamilyId,
    expandedSubspeciesIds,
    expandedBreedIds,
    highlightedContinent,
  );

  const handleSelect = useCallback((node: TaxonNode | null) => {
    if (!node) { setSelectedNodeId(null); return; }

    // FAMILY node click → focus / unfocus
    if (node.rank === "FAMILY") {
      const slug = node.familySlug ?? null;
      if (slug === focusedFamilySlug) {
        setFocus(null);
        setExpandedSubspeciesIds(new Set());
        setExpandedBreedIds(new Set());
        setHighlightedContinent(null);
      } else {
        setFocus(slug);
        setExpandedSubspeciesIds(new Set());
        setExpandedBreedIds(new Set());
        setHighlightedContinent(null);
        pendingZoomId.current = node.id;
      }
      return;
    }

    // SPECIES with subspecies/breeds → toggle expansion
    if (node.rank === "SPECIES") {
      const fullNode = walkFind(annotatedData, node.id);
      const hasSubspecies = fullNode?.children?.some(c => c.rank === "SUBSPECIES") ?? false;
      const hasBreeds = fullNode?.children?.some(c => c.rank === "BREED_GROUP") ?? false;

      if (hasSubspecies) {
        setExpandedSubspeciesIds(prev => {
          const next = new Set(prev);
          if (next.has(node.id)) next.delete(node.id);
          else { next.add(node.id); pendingZoomId.current = node.id; }
          return next;
        });
      } else if (hasBreeds) {
        setExpandedBreedIds(prev => {
          const next = new Set(prev);
          if (next.has(node.id)) next.delete(node.id);
          else { next.add(node.id); pendingZoomId.current = node.id; }
          return next;
        });
      }
    }

    // Toggle selection: clicking same node deselects
    setSelectedNodeId(selectedNodeId === node.id ? null : node.id);
  }, [focusedFamilySlug, selectedNodeId, setFocus, setSelectedNodeId]);

  const handleCollapseFamily = useCallback(() => {
    setFocus(null);
    setExpandedSubspeciesIds(new Set());
    setExpandedBreedIds(new Set());
    setHighlightedContinent(null);
  }, [setFocus]);

  const selectedInTree = useMemo(
    () => selected ? (walkFind(treeData, selected.id) ?? selected) : null,
    [selected, treeData],
  );

  const navContext = useMemo(
    () => selected ? findNavContext(treeData, selected.id) : null,
    [selected, treeData],
  );

  const focusedFamilyNode = useMemo(
    () => focusedFamilyId ? walkFind(annotatedData, focusedFamilyId) : null,
    [focusedFamilyId],
  );

  const breadcrumbPath = useMemo(
    () => selected ? getPathToNode(treeData, selected.id) : [],
    [selected, treeData],
  );

  const subfamiliesForPanel = useMemo(() => {
    if (!focusedFamilyId || !focusedFamilyNode) return [];
    return (focusedFamilyNode.children ?? []).filter(
      c => c.rank === "SUBFAMILY" || c.rank === "TRIBE",
    );
  }, [focusedFamilyId, focusedFamilyNode]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "A") return;
      if (e.key === "Escape" && focusedFamilySlug) { handleCollapseFamily(); return; }
      if (!selected || !navContext) return;
      const { parent, siblings, index } = navContext;
      if (e.key === "ArrowLeft") {
        if (siblings.length > 1) handleSelect(siblings[(index - 1 + siblings.length) % siblings.length]);
      } else if (e.key === "ArrowRight") {
        if (siblings.length > 1) handleSelect(siblings[(index + 1) % siblings.length]);
      } else if (e.key === "ArrowUp" && parent) {
        e.preventDefault();
        handleSelect(parent);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, navContext, handleSelect, focusedFamilySlug, handleCollapseFamily]);

  const familyCount = useMemo(() => {
    let n = 0;
    function walk(node: TaxonNode) {
      if (node.rank === "FAMILY") { n++; return; }
      node.children?.forEach(walk);
    }
    walk(annotatedData);
    return n;
  }, []);

  const btnBase: React.CSSProperties = {
    padding: "6px 14px",
    borderRadius: 6,
    border: "1px solid",
    fontSize: 13,
    cursor: "pointer",
  };

  const inFamilyFocus = focusedFamilySlug !== null;
  const hasContinentData = selected?.rank === "SPECIES" || selected?.rank === "SUBSPECIES";

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "#0f1117",
      color: "#e0e0e0",
      fontFamily: "'SF Pro Text', 'Helvetica Neue', system-ui, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        borderBottom: "1px solid #1e2030",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>Systema Naturae</span>
          <span style={{ fontSize: 13, color: "#555" }}>
            {inFamilyFocus
              ? (focusedFamilyNode?.commonName ?? focusedFamilyNode?.name ?? "")
              : `Animal taxonomy · ${familyCount} families`}
          </span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {inFamilyFocus && (
            <button
              onClick={handleCollapseFamily}
              style={{ ...btnBase, borderColor: "#303048", background: "#141420", color: "#8899cc", marginRight: 4 }}
            >
              ← All families
            </button>
          )}
          {(["radial", "vertical"] as const).map(l => (
            <button
              key={l}
              onClick={() => setLayout(l)}
              style={{
                ...btnBase,
                borderColor: layout === l ? "#3a3d50" : "#1e2030",
                background: layout === l ? "#1e2030" : "transparent",
                color: layout === l ? "#e0e0e0" : "#555",
              }}
            >
              {l === "radial" ? "⊕ Radial" : "⇒ Vertical"}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <FamilyTree
            data={treeData}
            layout={layout}
            onSelect={handleSelect}
            selectedId={selected?.id ?? null}
            pendingZoomId={pendingZoomId}
            highlightedNodeIds={highlightedNodeIds}
            colorTheme={colorTheme}
            focusedFamilySlug={focusedFamilySlug}
          />
        </div>

        {/* Sidebar */}
        <div style={{
          width: 380,
          borderLeft: "1px solid #1e2030",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}>
          {inFamilyFocus && hasContinentData && (
            <HabitatMap
              selectedContinents={selected?.continents ?? []}
              highlightedContinent={highlightedContinent}
              onContinentClick={c => setHighlightedContinent(prev => prev === c ? null : c)}
            />
          )}
          {breadcrumbPath.length > 1 && (
            <Breadcrumb path={breadcrumbPath} onSelect={handleSelect} />
          )}
          {selected && navContext && (
            <NodeNav
              parent={navContext.parent}
              siblings={navContext.siblings}
              index={navContext.index}
              onNavigate={handleSelect}
            />
          )}
          <div style={{ flex: 1, overflowY: "auto" }}>
            <UnifiedInfoPanel
              node={selectedInTree}
              onSelect={handleSelect}
              findNodeById={findNodeById}
              onFocusFamily={slug => setFocus(slug)}
              focusedFamilySlug={focusedFamilySlug}
              subfamilies={subfamiliesForPanel}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
