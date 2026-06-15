import type { TaxonNode } from "@shared/types";

interface Props {
  path: TaxonNode[];
  onSelect: (node: TaxonNode) => void;
}

// Ranks shown in breadcrumb — skip the very top of the tree
const SKIP_RANKS = new Set(["KINGDOM", "PHYLUM"]);

export default function Breadcrumb({ path, onSelect }: Props) {
  const crumbs = path.filter(n => !SKIP_RANKS.has(n.rank));
  if (crumbs.length < 2) return null;

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      alignItems: "center",
      gap: 2,
      padding: "8px 16px 0",
      fontSize: 11,
      color: "#444",
      lineHeight: 1.5,
    }}>
      {crumbs.map((node, i) => {
        const isLast = i === crumbs.length - 1;
        const label = node.commonName ?? node.name;
        return (
          <span key={node.id} style={{ display: "flex", alignItems: "center", gap: 2 }}>
            {i > 0 && <span style={{ color: "#2a2a3a", userSelect: "none" }}>›</span>}
            <button
              onClick={() => !isLast && onSelect(node)}
              style={{
                background: "none",
                border: "none",
                padding: "1px 3px",
                borderRadius: 3,
                cursor: isLast ? "default" : "pointer",
                color: isLast ? "#aaa" : "#3a4a6a",
                fontStyle: ["GENUS", "SPECIES", "SUBSPECIES"].includes(node.rank) ? "italic" : "normal",
                fontSize: 11,
              }}
              onMouseEnter={e => { if (!isLast) e.currentTarget.style.color = "#6688bb"; }}
              onMouseLeave={e => { if (!isLast) e.currentTarget.style.color = "#3a4a6a"; }}
            >
              {label}
            </button>
          </span>
        );
      })}
    </div>
  );
}
