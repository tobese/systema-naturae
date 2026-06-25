import type { TaxonNode } from "@shared/types";
import { PORTAL_THEME } from "../colors";
import { COLOR_REGISTRY } from "../colorRegistry";

interface Props {
  path: TaxonNode[];
  onSelect: (node: TaxonNode) => void;
}

const SKIP_RANKS = new Set(["KINGDOM"]);

function pillColor(node: TaxonNode): string {
  if (node.rank === "PHYLUM") return "#9a8858";
  if (node.rank === "CLASS") return PORTAL_THEME.lineageColors[node.name] ?? "#7a9fc2";
  if (node.rank === "ORDER") {
    const className = node.className ?? "";
    const base = PORTAL_THEME.lineageColors[className] ?? "#666";
    const hash = node.name.split("").reduce((s, c) => s + c.charCodeAt(0), 0);
    const shift = (hash % 30) - 15;
    const h = parseInt(base.slice(1, 3), 16);
    const s2 = parseInt(base.slice(3, 5), 16);
    const l = parseInt(base.slice(5, 7), 16);
    const clamp = (n: number) => Math.max(0, Math.min(255, Math.round(n)));
    return "#" + [h, s2, l].map((v, i) => clamp(v + (i === 2 ? shift : 0)).toString(16).padStart(2, "0")).join("");
  }
  if (node.rank === "FAMILY") return "#F5F5F5";
  if (node.familySlug) {
    const theme = COLOR_REGISTRY[node.familySlug];
    if (node.rank === "SUBFAMILY" || node.rank === "TRIBE") return theme?.subfamilyColors[node.name] ?? "#8899bb";
    if (node.lineage) return theme?.lineageColors[node.lineage] ?? "#888";
  }
  if (node.rank === "GENUS") return "#b5cd6a";
  if (node.rank === "SPECIES" || node.rank === "SUBSPECIES") return "#e6a817";
  return "#888";
}

function bgForColor(color: string): string {
  return color + "22";
}

export default function StatisticsHeader({ path, onSelect }: Props) {
  const filtered = path.filter(n => !SKIP_RANKS.has(n.rank));
  if (filtered.length === 0) return null;

  return (
    <div style={{
      padding: "10px 12px 6px",
      borderBottom: "1px solid #1a1a2a",
      flexShrink: 0,
      overflowX: "auto",
      scrollbarWidth: "none",
    }}>
      <style>{`
        .stats-header::-webkit-scrollbar { display: none; }
      `}</style>
      <div className="stats-header" style={{ display: "flex", alignItems: "center", gap: 6, minWidth: "max-content" }}>
        {filtered.map((node, i) => {
          const color = pillColor(node);
          const isLast = i === filtered.length - 1;
          const label = node.commonName ?? node.name;

          return (
            <div key={node.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {i > 0 && (
                <span style={{ color: "#333", fontSize: 10, userSelect: "none" }}>›</span>
              )}
              <button
                onClick={() => onSelect(node)}
                title={node.rank}
                style={{
                  background: bgForColor(color),
                  border: `1px solid ${color}44`,
                  borderRadius: 12,
                  color: isLast ? "#e0e0e0" : "#8899bb",
                  fontSize: isLast ? 12 : 10,
                  fontWeight: isLast ? 600 : 400,
                  padding: "3px 10px",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  lineHeight: 1.4,
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => { e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = color + "aa"; }}
                onMouseLeave={e => { e.currentTarget.style.color = isLast ? "#e0e0e0" : "#8899bb"; e.currentTarget.style.borderColor = `${color}44`; }}
              >
                {label}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
