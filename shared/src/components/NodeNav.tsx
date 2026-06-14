import type { TaxonNode } from "../types";

interface Props {
  parent: TaxonNode | null;
  siblings: TaxonNode[];
  index: number;
  onNavigate: (node: TaxonNode) => void;
}

const btn: React.CSSProperties = {
  background: "none",
  border: "none",
  cursor: "pointer",
  padding: "3px 7px",
  borderRadius: 4,
  fontSize: 15,
  lineHeight: 1,
  color: "#555",
};

export default function NodeNav({ parent, siblings, index, onNavigate }: Props) {
  const hasSiblings = siblings.length > 1;

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "5px 10px",
      borderBottom: "1px solid #1a1a2a",
      flexShrink: 0,
      minHeight: 32,
      gap: 6,
    }}>
      {parent ? (
        <button
          onClick={() => onNavigate(parent)}
          title={`Up to ${parent.commonName ?? parent.name}`}
          style={{ ...btn, color: "#777", fontSize: 12, display: "flex", alignItems: "center", gap: 4, maxWidth: 140 }}
          onMouseEnter={e => { e.currentTarget.style.color = "#ccc"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "#777"; }}
        >
          <span style={{ flexShrink: 0 }}>↑</span>
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {parent.commonName ?? parent.name}
          </span>
        </button>
      ) : <div />}

      {hasSiblings && (
        <div style={{ display: "flex", alignItems: "center", gap: 2, flexShrink: 0 }}>
          <button
            onClick={() => onNavigate(siblings[(index - 1 + siblings.length) % siblings.length])}
            title="Previous (←)"
            style={btn}
            onMouseEnter={e => { e.currentTarget.style.color = "#ccc"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "#555"; }}
          >‹</button>
          <span style={{ fontSize: 10, color: "#444", minWidth: 28, textAlign: "center" }}>
            {index + 1}/{siblings.length}
          </span>
          <button
            onClick={() => onNavigate(siblings[(index + 1) % siblings.length])}
            title="Next (→)"
            style={btn}
            onMouseEnter={e => { e.currentTarget.style.color = "#ccc"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "#555"; }}
          >›</button>
        </div>
      )}
    </div>
  );
}
