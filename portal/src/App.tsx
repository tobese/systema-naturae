import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import FamilyTree from "@shared/components/FamilyTree";
import InfoPanel from "./components/InfoPanel";
import NodeNav from "@shared/components/NodeNav";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "./types";
import { PORTAL_THEME, annotatePortalTree } from "./colors";
import rawData from "../data/taxonomy.json";

const treeData = annotatePortalTree(rawData as PortalNode);

function walkFind(node: PortalNode, id: string): PortalNode | null {
  if (node.id === id) return node;
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
}

function findNavContext(
  tree: PortalNode,
  targetId: string,
): { parent: TaxonNode | null; siblings: TaxonNode[]; index: number } {
  if (tree.id === targetId) return { parent: null, siblings: [], index: 0 };

  function walk(node: PortalNode): { parent: TaxonNode; siblings: TaxonNode[]; index: number } | null {
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
  const [selected, setSelected] = useState<PortalNode | null>(null);
  const pendingZoomId = useRef<string | null>(null);

  const handleSelect = useCallback((node: TaxonNode | null) => {
    if (!node) { setSelected(null); return; }
    const pn = node as PortalNode;
    setSelected(prev => prev?.id === pn.id ? null : pn);
  }, []);

  const selectedInTree = useMemo(
    () => selected ? (walkFind(treeData, selected.id) ?? selected) : null,
    [selected],
  );

  const navContext = useMemo(
    () => selected ? findNavContext(treeData, selected.id) : null,
    [selected],
  );

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
          <span style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>Systema Naturae</span>
          <span style={{ fontSize: 13, color: "#555" }}>Animal taxonomy · 8 families</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
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
            colorTheme={PORTAL_THEME}
          />
        </div>
        <div style={{
          width: 340,
          borderLeft: "1px solid #1e2030",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
          overflowY: "auto",
        }}>
          {selected && navContext && (
            <NodeNav
              parent={navContext.parent}
              siblings={navContext.siblings}
              index={navContext.index}
              onNavigate={handleSelect}
            />
          )}
          <InfoPanel node={selectedInTree} onSelect={handleSelect} />
        </div>
      </div>
    </div>
  );
}
