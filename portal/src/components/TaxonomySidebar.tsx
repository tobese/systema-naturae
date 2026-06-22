import { useState, useEffect } from "react";
import type { TaxonNode } from "@shared/types";

interface Props {
  data: TaxonNode;
  focusedClassId: string | null;
  focusedFamilySlug: string | null;
  selectedId: string | null;
  onSelect: (node: TaxonNode) => void;
  onFocusFamily: (slug: string | null) => void;
  onFocusClass: (id: string | null) => void;
}

const CLASS_COLORS: Record<string, string> = {
  mammalia: "#C87941",
  aves: "#3A8090",
  reptilia: "#4A8C5C",
  chondrichthyes: "#5A78A0",
  amphibia: "#7CB84A",
  actinopterygii: "#3A8FA8",
  insecta: "#C8A830",
  arachnida: "#A84868",
};

function countChildren(node: TaxonNode, rank: string): number {
  let total = 0;
  function walk(n: TaxonNode) {
    if (n.rank === rank) total++;
    n.children?.forEach(walk);
  }
  node.children?.forEach(walk);
  return total;
}

// All CLASS nodes expanded by default so the user sees the full hierarchy.
// KINGDOM + all CLASSES are pre-expanded. ORDERS and deeper start collapsed.
function defaultExpanded(data: TaxonNode): Set<string> {
  const s = new Set<string>();
  function walk(n: TaxonNode) {
    if (n.rank === "KINGDOM" || n.rank === "CLASS") s.add(n.id);
    n.children?.forEach(walk);
  }
  walk(data);
  return s;
}

const indentGuide: Record<string, string | number> = {
  display: "inline-block",
  width: 1,
  height: "100%",
  background: "#1e2030",
  position: "absolute",
  left: 0,
  top: 0,
};

export default function TaxonomySidebar({
  data,
  focusedClassId,
  focusedFamilySlug,
  selectedId,
  onSelect,
}: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(() => defaultExpanded(data));

  // Auto-expand focused class's children
  useEffect(() => {
    if (!focusedClassId) return;
    setExpanded(prev => {
      const next = new Set(prev);
      function walk(n: TaxonNode) {
        if (n.id === focusedClassId || n.rank === "FAMILY" || n.rank === "ORDER") {
          next.add(n.id);
        }
        n.children?.forEach(walk);
      }
      walk(data);
      return next;
    });
  }, [focusedClassId, data]);

  // Auto-expand focused family's ancestors + genus children
  useEffect(() => {
    if (!focusedFamilySlug) return;
    setExpanded(prev => {
      const next = new Set(prev);
      function walk(n: TaxonNode): boolean {
        if (n.rank === "FAMILY" && n.familySlug === focusedFamilySlug) {
          next.add(n.id);
          // Also expand genus children
          n.children?.forEach(c => { if (c.rank === "GENUS") next.add(c.id); });
          return true;
        }
        if (n.children?.some(c => walk(c))) {
          next.add(n.id);
          return true;
        }
        return false;
      }
      walk(data);
      return next;
    });
  }, [focusedFamilySlug, data]);

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div style={{
      padding: "6px 0",
      overflowY: "auto",
      overflowX: "hidden",
      height: "100%",
      fontSize: 12,
      userSelect: "none",
    }}>
      <div style={{ padding: "0 8px 6px 8px", fontSize: 10, color: "#4a4a5a", letterSpacing: "0.05em", textTransform: "uppercase" }}>
        Explorer
      </div>
      {renderNode(data, expanded, focusedClassId, focusedFamilySlug, selectedId, onSelect, toggle, 0)}
    </div>
  );
}

function renderNode(
  node: TaxonNode,
  expanded: Set<string>,
  focusedClassId: string | null,
  focusedFamilySlug: string | null,
  selectedId: string | null,
  onSelect: (node: TaxonNode) => void,
  toggle: (id: string) => void,
  depth: number,
): React.ReactNode {
  if (!node.children || node.children.length === 0) return null;

  const isClass = node.rank === "CLASS";
  const isOrder = node.rank === "ORDER";
  const isFamily = node.rank === "FAMILY";
  const isDeep = depth >= 3; // genus+

  const classColor = node.className ? CLASS_COLORS[node.className] : undefined;
  const accentColor = classColor ?? "#666";
  const isOpen = expanded.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const isFocusTarget = (isClass && node.id === focusedClassId) || (isFamily && node.familySlug === focusedFamilySlug);
  const isSelected = node.id === selectedId;

  // Show children for top-level containers and CLASS all the time.
  // For ORDER, only show when class is focused to avoid clutter.
  // For FAMILY, always show if open.
  // For genus+, only show when family is focused.
  const showChildren = (() => {
    if (depth === 0 || isClass) return true; // kingdom/phylum root + all classes
    if (isOrder) return focusedClassId !== null;
    if (isFamily) return true;
    return focusedFamilySlug !== null && node.familySlug === focusedFamilySlug;
  })();

  // Child count label
  const childLabel = (() => {
    if (isClass) return `${countChildren(node, "ORDER")} orders`;
    if (isOrder) return `${countChildren(node, "FAMILY")} families`;
    if (isFamily) return `${countChildren(node, "GENUS")} genera`;
    return undefined;
  })();

  // Species count for families
  const speciesCount = isFamily ? countChildren(node, "SPECIES") : 0;

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          position: "relative",
          paddingLeft: depth * 16 + 8,
          paddingRight: 8,
          height: hasChildren ? 28 : 24,
          background: isFocusTarget ? "#141e28" : isSelected ? "#1a2030" : "transparent",
          cursor: hasChildren || !isDeep ? "pointer" : "default",
          borderLeft: isFocusTarget ? "2px solid " + accentColor : "2px solid transparent",
        }}
        onClick={() => {
          if (isDeep && hasChildren) toggle(node.id);
          if (isClass || isFamily || !isDeep) onSelect(node);
        }}
        onMouseEnter={e => {
          if (!isFocusTarget && !isSelected)
            (e.currentTarget as HTMLElement).style.background = "#12141e";
        }}
        onMouseLeave={e => {
          if (!isFocusTarget && !isSelected)
            (e.currentTarget as HTMLElement).style.background = "transparent";
        }}
        title={node.commonName ?? node.name}
      >
        {/* Expand/collapse arrow */}
        {hasChildren ? (
          <span
            onClick={(e) => { e.stopPropagation(); toggle(node.id); }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 16,
              height: 16,
              flexShrink: 0,
              fontSize: 9,
              color: "#5a5a7a",
              borderRadius: 3,
              marginRight: 2,
            }}
          >
            {isOpen ? "▼" : "▶"}
          </span>
        ) : (
          <span style={{ width: 18, flexShrink: 0 }} />
        )}

        {/* Color dot */}
        <span style={{
          display: "inline-block",
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: accentColor,
          flexShrink: 0,
          marginRight: 5,
          opacity: isDeep ? 0.5 : 1,
        }} />

        {/* Name */}
        <span style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          color: isFocusTarget ? "#e0e0f0" : isSelected ? "#d0d0e8" : isDeep ? "#6a7a8a" : "#b0b8c8",
          fontWeight: isFocusTarget ? 500 : 400,
          fontSize: isClass ? 11 : isOrder ? 10 : isFamily ? 9 : 7,
        }}>
          {node.commonName && ["KINGDOM","PHYLUM","CLASS","ORDER","FAMILY"].includes(node.rank) ? node.commonName : node.name}
        </span>

        {/* Count badges */}
        {childLabel && !isOpen && (
          <span style={{
            marginLeft: 6,
            fontSize: 10,
            color: "#4a5568",
            flexShrink: 0,
          }}>
            {childLabel}
          </span>
        )}
        {isFamily && speciesCount > 0 && !isOpen && (
          <span style={{
            marginLeft: 3,
            fontSize: 10,
            color: "#3a4558",
            flexShrink: 0,
          }}>
            · {speciesCount} sp.
          </span>
        )}
      </div>

      {/* Children */}
      {isOpen && hasChildren && showChildren && (
        <div>
            {node.children!.map((c) => (
            <div key={c.id} style={{ position: "relative" }}>
              {/* Vertical indent guide */}
              {depth > 0 && (
                <div style={{
                  ...indentGuide as React.CSSProperties,
                  left: depth * 16 + 4,
                  height: "100%",
                  top: 0,
                }} />
              )}
              {renderNode(c, expanded, focusedClassId, focusedFamilySlug, selectedId, onSelect, toggle, depth + 1)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
