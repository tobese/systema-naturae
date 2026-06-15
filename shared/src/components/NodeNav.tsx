import type { TaxonNode, ColorTheme } from "../types";

interface Props {
  parent: TaxonNode | null;
  siblings: TaxonNode[];
  index: number;
  onNavigate: (node: TaxonNode) => void;
  breadcrumbPath?: TaxonNode[];
  colorTheme?: ColorTheme;
}

const SKIP_RANKS = new Set(["KINGDOM", "PHYLUM"]);

function navColor(node: TaxonNode, theme: ColorTheme): string {
  if (node.rank === "FAMILY" || node.rank === "TRIBE") return "#e0e0e0";
  if (node.rank === "SUBFAMILY") return theme.subfamilyColors[node.name] ?? "#777";
  if (node.rank === "BREED_GROUP" || node.rank === "BREED") return theme.breedGroupColor;
  if (node.rank === "HYBRID_GROUP" || node.rank === "HYBRID") return theme.hybridColor;
  const lineage = node.lineage;
  if (lineage && theme.lineageColors[lineage]) return theme.lineageColors[lineage];
  return theme.subfamilyColors[lineage ?? ""] ?? "#666";
}

const btnBase: React.CSSProperties = {
  background: "none",
  border: "none",
  cursor: "pointer",
  padding: 0,
  lineHeight: 1,
};

export default function NodeNav({ siblings, index, onNavigate, breadcrumbPath, colorTheme }: Props) {
  const hasSiblings = siblings.length > 1;
  const path = (breadcrumbPath ?? []).filter(n => !SKIP_RANKS.has(n.rank));

  if (path.length === 0) return null;

  const theme: ColorTheme = colorTheme ?? {
    subfamilyColors: {}, lineageColors: {}, breedGroupColor: "#888", hybridColor: "#888",
  };

  const prev = siblings[(index - 1 + siblings.length) % siblings.length];
  const next = siblings[(index + 1) % siblings.length];

  return (
    <div style={{
      padding: "8px 12px",
      borderBottom: "1px solid #1a1a2a",
      flexShrink: 0,
    }}>
      {path.map((node, i) => {
        const isSelected = i === path.length - 1;
        const color = navColor(node, theme);
        const indent = i * 10;
        const label = node.commonName ?? node.name;

        return (
          <div
            key={node.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "2px 0",
              paddingLeft: indent,
            }}
          >
            <div style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: color,
              flexShrink: 0,
              opacity: isSelected ? 1 : 0.7,
            }} />

            {isSelected && hasSiblings && (
              <div style={{ display: "flex", alignItems: "center", gap: 2, flexShrink: 0 }}>
                <button
                  onClick={() => onNavigate(prev)}
                  title="Previous (←)"
                  style={{ ...btnBase, fontSize: 13, color: "#555", padding: "0 2px" }}
                  onMouseEnter={e => { e.currentTarget.style.color = "#ccc"; }}
                  onMouseLeave={e => { e.currentTarget.style.color = "#555"; }}
                >‹</button>
                <span style={{ fontSize: 10, color: "#444", minWidth: 22, textAlign: "center" }}>
                  {index + 1}/{siblings.length}
                </span>
                <button
                  onClick={() => onNavigate(next)}
                  title="Next (→)"
                  style={{ ...btnBase, fontSize: 13, color: "#555", padding: "0 2px" }}
                  onMouseEnter={e => { e.currentTarget.style.color = "#ccc"; }}
                  onMouseLeave={e => { e.currentTarget.style.color = "#555"; }}
                >›</button>
              </div>
            )}

            <button
              onClick={() => !isSelected && onNavigate(node)}
              style={{
                ...btnBase,
                fontSize: isSelected ? 13 : 11,
                color: isSelected ? "#d0d0d0" : "#556",
                fontWeight: isSelected ? 600 : 400,
                cursor: isSelected ? "default" : "pointer",
                textAlign: "left",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                maxWidth: 220,
              }}
              onMouseEnter={e => { if (!isSelected) e.currentTarget.style.color = "#aaa"; }}
              onMouseLeave={e => { if (!isSelected) e.currentTarget.style.color = "#556"; }}
            >
              {label}
            </button>
          </div>
        );
      })}
    </div>
  );
}
