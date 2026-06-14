import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import FamilyTree from "@shared/components/FamilyTree";
import InfoPanel from "./components/InfoPanel";
import NodeNav from "@shared/components/NodeNav";
import HabitatMap from "@shared/components/HabitatMap";
import type { TaxonNode } from "@shared/types";
import { EQUIDAE_THEME } from "./colors";
import equidaeData from "./data/equidae.json";

function walkFind(node: TaxonNode, id: string): TaxonNode | null {
  if (node.id === id) return node;
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
}

const fullData = equidaeData as TaxonNode;
const DOMESTIC_HORSE_ID = "DOMESTIC_HORSE";

function collapseTree(node: TaxonNode): TaxonNode {
  if (node.id === DOMESTIC_HORSE_ID) {
    const { children: _c, ...rest } = node;
    return rest as TaxonNode;
  }
  if (node.rank === "SPECIES" && node.children?.every(c => c.rank === "SUBSPECIES")) {
    const { children: _c, ...rest } = node;
    return rest as TaxonNode;
  }
  if (!node.children) return node;
  return { ...node, children: node.children.map(collapseTree) };
}

const collapsedData = collapseTree(fullData);

function expandOneSubspecies(base: TaxonNode, full: TaxonNode, targetId: string): TaxonNode {
  if (base.id === targetId) return walkFind(full, targetId) ?? base;
  if (!base.children) return base;
  return { ...base, children: base.children.map(c => expandOneSubspecies(c, full, targetId)) };
}

function findNavContext(
  tree: TaxonNode,
  targetId: string
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
  const [selected, setSelected] = useState<TaxonNode | null>(null);
  const [breedsExpanded, setBreedsExpanded] = useState(false);
  const [expandedSubspeciesId, setExpandedSubspeciesId] = useState<string | null>(null);
  const [highlightedContinent, setHighlightedContinent] = useState<string | null>(null);
  const pendingZoomId = useRef<string | null>(null);

  const treeData = useMemo<TaxonNode>(() => {
    const base = breedsExpanded ? fullData : collapsedData;
    if (!expandedSubspeciesId) return base;
    return expandOneSubspecies(base, fullData, expandedSubspeciesId);
  }, [breedsExpanded, expandedSubspeciesId]);

  const handleSelect = useCallback((node: TaxonNode | null) => {
    setSelected(prev => {
      const isSame = prev?.id === node?.id;

      if (node?.rank === "SPECIES" && node.id !== DOMESTIC_HORSE_ID) {
        const fullNode = walkFind(fullData, node.id);
        const hasSubspecies = fullNode?.children?.some(c => c.rank === "SUBSPECIES");
        if (hasSubspecies) {
          if (expandedSubspeciesId === node.id) {
            setExpandedSubspeciesId(null);
            return null;
          } else {
            pendingZoomId.current = node.id;
            setExpandedSubspeciesId(node.id);
            return node;
          }
        }
      }

      if (node?.id === DOMESTIC_HORSE_ID) {
        if (!breedsExpanded) {
          pendingZoomId.current = DOMESTIC_HORSE_ID;
          setBreedsExpanded(true);
          return node;
        } else if (isSame) {
          setBreedsExpanded(false);
          return null;
        }
      }

      return isSame ? null : node;
    });
  }, [breedsExpanded, expandedSubspeciesId]);

  const handleCollapse = useCallback(() => {
    setBreedsExpanded(false);
    setSelected(null);
  }, []);

  const handleCollapseSubspecies = useCallback(() => {
    setExpandedSubspeciesId(null);
    setSelected(null);
  }, []);

  const selectedInTree = useMemo(
    () => selected ? (walkFind(treeData, selected.id) ?? selected) : null,
    [selected, treeData]
  );

  const navContext = useMemo(
    () => selected ? findNavContext(treeData, selected.id) : null,
    [selected, treeData]
  );

  const highlightedNodeIds = useMemo<Set<string> | null>(() => {
    if (!highlightedContinent) return null;
    const ids = new Set<string>();
    const continent = highlightedContinent;
    function walk(node: TaxonNode) {
      if (node.continents?.includes(continent)) ids.add(node.id);
      node.children?.forEach(walk);
    }
    walk(fullData);
    return ids;
  }, [highlightedContinent]);

  useEffect(() => {
    if (!selected || !navContext) return;
    const { parent, siblings, index } = navContext;

    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "A") return;
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
  }, [selected, navContext, handleSelect]);

  const speciesCount = useMemo(() => {
    let count = 0;
    function walk(node: TaxonNode) {
      if (node.rank === "SPECIES") count++;
      node.children?.forEach(walk);
    }
    walk(fullData);
    return count;
  }, []);

  const btnBase: React.CSSProperties = {
    padding: "6px 14px",
    borderRadius: 6,
    border: "1px solid",
    fontSize: 13,
    cursor: "pointer",
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "#0f1117",
      color: "#e0e0e0",
      fontFamily: "'SF Pro Text', 'Helvetica Neue', system-ui, sans-serif",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        borderBottom: "1px solid #1e2030",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>Equidae</span>
          <span style={{ fontSize: 13, color: "#555" }}>Family Tree · {speciesCount} species</span>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {expandedSubspeciesId && (
            <button
              onClick={handleCollapseSubspecies}
              style={{ ...btnBase, borderColor: "#303048", background: "#141420", color: "#8899cc", marginRight: 4 }}
            >
              ← Collapse subspecies
            </button>
          )}
          {breedsExpanded && (
            <button
              onClick={handleCollapse}
              style={{ ...btnBase, borderColor: "#3a3020", background: "#1a1510", color: EQUIDAE_THEME.breedGroupColor, marginRight: 4 }}
            >
              ← Full tree
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

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <FamilyTree
            data={treeData}
            layout={layout}
            onSelect={handleSelect}
            selectedId={selected?.id ?? null}
            pendingZoomId={pendingZoomId}
            highlightedNodeIds={highlightedNodeIds}
            colorTheme={EQUIDAE_THEME}
            specialNodeId={DOMESTIC_HORSE_ID}
          />
        </div>
        <div style={{
          width: 380,
          borderLeft: "1px solid #1e2030",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}>
          <HabitatMap
            selectedContinents={selected?.continents ?? []}
            highlightedContinent={highlightedContinent}
            onContinentClick={c => setHighlightedContinent(prev => prev === c ? null : c)}
          />
          {selected && navContext && (
            <NodeNav
              parent={navContext.parent}
              siblings={navContext.siblings}
              index={navContext.index}
              onNavigate={handleSelect}
            />
          )}
          <div style={{ flex: 1, overflowY: "auto" }}>
            <InfoPanel
              node={selectedInTree}
              onSelect={handleSelect}
              findNodeById={(id) => walkFind(fullData, id)}
              subfamilies={[]}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
