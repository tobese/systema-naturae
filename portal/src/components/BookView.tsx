import { useState, useEffect } from "react";
import type { TaxonNode } from "@shared/types";
import { getClassColor, getOrderColor } from "../colors";

interface BookViewProps {
  data: TaxonNode;
  selectedId: string | null;
  onSelect: (node: TaxonNode | null) => void;
}

// Find path from root to target node for auto-expanding
function findPathToNode(node: TaxonNode, targetId: string, currentPath: string[] = []): string[] | null {
  const path = [...currentPath, node.id];
  if (node.id === targetId) return path;

  // Check compressed speciesList
  if (node.speciesList) {
    const foundSp = node.speciesList.find(s => s.id === targetId);
    if (foundSp) {
      return [...path, foundSp.id];
    }
  }

  for (const child of node.children ?? []) {
    const found = findPathToNode(child, targetId, path);
    if (found) return found;
  }

  return null;
}

export default function BookView({ data, selectedId, onSelect }: BookViewProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Auto-expand parents when selectedId changes
  useEffect(() => {
    if (!selectedId) return;
    const path = findPathToNode(data, selectedId);
    if (path) {
      setExpandedIds(prev => {
        const next = new Set(prev);
        // Add all elements of the path except the target itself
        path.slice(0, -1).forEach(id => next.add(id));
        return next;
      });

      // Allow DOM to update, then scroll the selected node into view
      setTimeout(() => {
        const el = document.getElementById(`book-node-${selectedId}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }, 100);
    }
  }, [selectedId, data]);

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleExpandAll = () => {
    const ids = new Set<string>();
    function collect(n: TaxonNode) {
      if (n.rank !== "SPECIES" && n.rank !== "SUBSPECIES") {
        ids.add(n.id);
        n.children?.forEach(collect);
      }
    }
    collect(data);
    setExpandedIds(ids);
  };

  const handleCollapseAll = () => {
    setExpandedIds(new Set());
  };

  // Helper to count physical + compressed species under any node
  const countAllSpecies = (node: TaxonNode): number => {
    if (node.rank === "SPECIES") return 1;
    let count = 0;
    if (node.speciesList) {
      count += node.speciesList.length;
    }
    node.children?.forEach(c => {
      count += countAllSpecies(c);
    });
    return count;
  };

  // Render nodes recursively
  const renderNode = (node: TaxonNode, depth: number = 0, currentClassName?: string, currentOrderName?: string) => {
    const isExpanded = expandedIds.has(node.id);
    const isSelected = selectedId === node.id;

    const nextClassName = node.rank === "CLASS" ? node.name : currentClassName;
    const nextOrderName = node.rank === "ORDER" ? node.name : currentOrderName;

    // Resolve color theme based on rank and lineage
    let color = "#888888";
    if (nextClassName) {
      color = getClassColor(nextClassName);
      if (nextOrderName && node.rank !== "CLASS") {
        color = getOrderColor(nextClassName, nextOrderName);
      }
    }

    if (node.rank === "SPECIES") {
      return (
        <div
          key={node.id}
          id={`book-node-${node.id}`}
          onClick={() => onSelect(node)}
          style={{
            padding: "8px 12px",
            margin: "4px 0",
            borderRadius: 4,
            cursor: "pointer",
            background: isSelected ? "rgba(100, 150, 255, 0.15)" : "transparent",
            borderLeft: `3px solid ${isSelected ? "#3b82f6" : "transparent"}`,
            fontSize: 13,
            transition: "all 0.15s ease",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
          onMouseEnter={e => {
            if (!isSelected) e.currentTarget.style.background = "rgba(255,255,255,0.03)";
          }}
          onMouseLeave={e => {
            if (!isSelected) e.currentTarget.style.background = "transparent";
          }}
        >
          <div>
            <span style={{ fontStyle: "italic", fontWeight: 500, color: "#f0f6fc" }}>{node.name}</span>
            {node.commonName && (
              <span style={{ marginLeft: 8, color: "#8b949e", fontSize: 12 }}>— {node.commonName}</span>
            )}
          </div>
          {node.extinct && (
            <span style={{ fontSize: 10, background: "#4a1515", color: "#ff8888", padding: "1px 5px", borderRadius: 3 }}>Extinct</span>
          )}
        </div>
      );
    }

    // Combine physical species and compressed flat species list for Genus rank
    const getSpeciesItems = () => {
      const items: TaxonNode[] = [];
      if (node.children) {
        items.push(...node.children.filter(c => c.rank === "SPECIES"));
      }
      if (node.speciesList) {
        items.push(...node.speciesList);
      }
      return items.sort((a, b) => a.name.localeCompare(b.name));
    };

    const hasChildren = (node.children && node.children.length > 0) || (node.speciesList && node.speciesList.length > 0);
    const nonSpeciesChildren = node.children?.filter(c => c.rank !== "SPECIES") ?? [];
    const speciesChildren = node.rank === "GENUS" ? getSpeciesItems() : [];

    const totalSpCount = countAllSpecies(node);

    // Padding & borders depending on rank level
    const borderStyle = depth > 0 ? `1px solid rgba(255,255,255,0.03)` : "none";
    const headerFontSize = Math.max(12, 18 - depth * 1.2);
    const headerWeight = depth === 0 ? 700 : depth === 1 ? 600 : 500;

    return (
      <div
        key={node.id}
        id={`book-node-${node.id}`}
        style={{
          borderBottom: borderStyle,
          paddingTop: depth === 0 ? 24 : 8,
          paddingBottom: depth === 0 ? 24 : 8,
          marginLeft: depth > 0 ? 12 : 0,
          borderLeft: depth === 0 ? `4px solid ${color}` : `1px dashed rgba(255,255,255,0.05)`,
          paddingLeft: depth === 0 ? 16 : 8,
        }}
      >
        <div
          onClick={() => {
            onSelect(node);
            if (hasChildren) toggleExpand(node.id);
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            cursor: "pointer",
            userSelect: "none",
            background: isSelected ? "rgba(255,255,255,0.04)" : "transparent",
            padding: "4px 8px",
            borderRadius: 4,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {hasChildren && (
              <span style={{
                fontSize: 10,
                color: "#555566",
                transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
                transition: "transform 0.15s ease",
                display: "inline-block",
                width: 8,
              }}>
                ▶
              </span>
            )}
            <span style={{
              fontSize: 10,
              fontWeight: 600,
              color,
              letterSpacing: "0.05em",
              background: `${color}15`,
              padding: "2px 6px",
              borderRadius: 3,
              textTransform: "uppercase",
            }}>
              {node.rank}
            </span>
            <span style={{
              fontSize: headerFontSize,
              fontWeight: headerWeight,
              color: isSelected ? "#3b82f6" : "#e2e8f0",
              fontFamily: node.rank === "GENUS" ? "monospace" : "inherit",
              fontStyle: node.rank === "GENUS" ? "italic" : "normal",
            }}>
              {node.name}
            </span>
            {node.commonName && (
              <span style={{ fontSize: headerFontSize - 2, color: "#8b949e" }}>
                ({node.commonName})
              </span>
            )}
          </div>
          <div style={{ fontSize: 11, color: "#555" }}>
            {totalSpCount > 0 && `${totalSpCount.toLocaleString()} species`}
          </div>
        </div>

        {isExpanded && (
          <div style={{ marginTop: 10, paddingLeft: 4 }}>
            {node.description && (
              <p style={{
                fontSize: 12,
                color: "#8b949e",
                lineHeight: 1.6,
                marginBottom: 12,
                fontStyle: "italic",
                paddingLeft: 8,
                borderLeft: "2px solid rgba(255,255,255,0.05)",
                maxWidth: 800,
              }}>
                {node.description}
              </p>
            )}

            {/* Recursively render child sections */}
            {nonSpeciesChildren.map(c => renderNode(c, depth + 1, nextClassName, nextOrderName))}

            {/* Render species items */}
            {speciesChildren.map(sp => renderNode(sp, depth + 1, nextClassName, nextOrderName))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100%",
      width: "100%",
      background: "#0c0e14",
      color: "#e2e8f0",
      overflow: "hidden",
    }}>
      {/* Tool bar inside main area */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 16px",
        background: "#0f111a",
        borderBottom: "1px solid #1e2030",
        flexShrink: 0,
      }}>
        <div style={{ fontSize: 12, color: "#555" }}>
          Use the nested outline below to explore the taxonomic tree chapter-by-chapter.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={handleExpandAll}
            style={{
              background: "transparent",
              border: "1px solid #30363d",
              borderRadius: 4,
              color: "#c9d1d9",
              padding: "4px 10px",
              fontSize: 11,
              cursor: "pointer",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "#21262d"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            Expand All
          </button>
          <button
            onClick={handleCollapseAll}
            style={{
              background: "transparent",
              border: "1px solid #30363d",
              borderRadius: 4,
              color: "#c9d1d9",
              padding: "4px 10px",
              fontSize: 11,
              cursor: "pointer",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "#21262d"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Book outline content */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "8px 24px 48px",
      }}>
        {renderNode(data, 0)}
      </div>
    </div>
  );
}
