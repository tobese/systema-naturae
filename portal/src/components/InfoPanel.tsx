import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "../types";
import { useWikipediaSummary } from "@shared/hooks/useWikipediaSummary";
import { PORTAL_THEME } from "../colors";
import { familyAppUrl } from "../utils/navUrl";

interface Props {
  node: PortalNode | null;
  onSelect: (node: TaxonNode) => void;
}

function accentFor(node: PortalNode): string {
  if (node.rank === "FAMILY") return "#F5F5F5";
  return PORTAL_THEME.lineageColors[node.lineage ?? node.name] ?? "#888";
}

function HomePanel() {
  return (
    <div style={{ padding: "24px 20px", color: "#555" }}>
      <div style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 20 }}>
        Explore the animal kingdom. Click any{" "}
        <span style={{ color: "#e0e0e0", fontWeight: 500 }}>family node</span>{" "}
        in the tree to open its dedicated app with the full species breakdown.
      </div>
      <div style={{ fontSize: 11, color: "#3a3a4a", lineHeight: 1.6 }}>
        <div style={{ marginBottom: 6 }}>White nodes → clickable family apps</div>
        <div style={{ marginBottom: 6 }}>Amber nodes → Mammalia orders</div>
        <div>Teal nodes → Aves orders</div>
      </div>
    </div>
  );
}

function ClassPanel({ node, onSelect }: { node: PortalNode; onSelect: (n: TaxonNode) => void }) {
  const accent = accentFor(node);
  const orders = node.children ?? [];
  const families = orders.flatMap(o => o.children ?? []) as PortalNode[];
  return (
    <div style={{ padding: "20px" }}>
      <div style={{ fontSize: 10, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
        Class
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>
        {node.commonName ?? node.name}
      </div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 16 }}>
        {node.name}
      </div>
      <div style={{ fontSize: 12, color: "#666", marginBottom: node.description ? 14 : 20 }}>
        {orders.length} {orders.length === 1 ? "order" : "orders"} · {families.length} {families.length === 1 ? "family" : "families"} in this collection
      </div>
      {node.description && (
        <div style={{ fontSize: 12, color: "#777", lineHeight: 1.7, marginBottom: 20 }}>
          {node.description}
        </div>
      )}
      <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
        Orders
      </div>
      {orders.map(o => (
        <button
          key={o.id}
          onClick={() => onSelect(o)}
          style={{
            display: "block",
            width: "100%",
            textAlign: "left",
            background: "none",
            border: "none",
            borderBottom: "1px solid #1a1a2a",
            padding: "8px 0",
            cursor: "pointer",
            color: "#8899bb",
            fontSize: 13,
          }}
        >
          {o.commonName ?? o.name}
          <span style={{ float: "right", color: "#333", fontSize: 11 }}>
            {(o.children ?? []).length} {(o.children ?? []).length === 1 ? "family" : "families"}
          </span>
        </button>
      ))}
    </div>
  );
}

function OrderPanel({ node, onSelect }: { node: PortalNode; onSelect: (n: TaxonNode) => void }) {
  const accent = accentFor(node);
  const families = (node.children ?? []) as PortalNode[];
  return (
    <div style={{ padding: "20px" }}>
      <div style={{ fontSize: 10, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
        Order
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>
        {node.commonName ?? node.name}
      </div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 16 }}>
        {node.name}
      </div>
      <div style={{ fontSize: 12, color: "#666", marginBottom: node.description ? 14 : 20 }}>
        {families.length} {families.length === 1 ? "family" : "families"} in this collection
      </div>
      {node.description && (
        <div style={{ fontSize: 12, color: "#777", lineHeight: 1.7, marginBottom: 20 }}>
          {node.description}
        </div>
      )}
      <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
        Families
      </div>
      {families.map(f => (
        <button
          key={f.id}
          onClick={() => onSelect(f)}
          style={{
            display: "block",
            width: "100%",
            textAlign: "left",
            background: "none",
            border: "none",
            borderBottom: "1px solid #1a1a2a",
            padding: "8px 0",
            cursor: "pointer",
            color: "#8899bb",
            fontSize: 13,
          }}
        >
          {f.commonName ?? f.name}
          <span style={{ float: "right", color: "#333", fontSize: 11 }}>
            {f.speciesCount} spp.
          </span>
        </button>
      ))}
    </div>
  );
}

function FamilyPanel({ node }: { node: PortalNode }) {
  const wikiTitle = node.commonName ?? node.name;
  const { data: wiki, loading } = useWikipediaSummary(wikiTitle);

  return (
    <div style={{ padding: "20px" }}>
      <div style={{ fontSize: 10, color: "#F5F5F5", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
        Family
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>
        {node.commonName ?? node.name}
      </div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 4 }}>
        {node.name}
      </div>
      {node.speciesCount !== undefined && (
        <div style={{ fontSize: 12, color: "#666", marginBottom: 16 }}>
          {node.speciesCount} species
        </div>
      )}

      {node.taxonomicNote && (
        <div style={{
          fontSize: 11,
          color: "#555",
          fontStyle: "italic",
          background: "#0a0a14",
          border: "1px solid #1a1a2a",
          borderRadius: 6,
          padding: "8px 10px",
          marginBottom: 16,
          lineHeight: 1.5,
        }}>
          {node.taxonomicNote}
        </div>
      )}

      {node.notableMembers && node.notableMembers.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
            Notable members
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {node.notableMembers.map(m => (
              <span key={m} style={{
                fontSize: 11,
                color: "#7788aa",
                background: "#0d0d1a",
                border: "1px solid #1e2030",
                borderRadius: 4,
                padding: "3px 8px",
              }}>
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div style={{ fontSize: 12, color: "#333", marginBottom: 16 }}>Loading…</div>
      )}
      {wiki?.extract && (
        <div style={{ fontSize: 12, color: "#666", lineHeight: 1.7, marginBottom: 20 }}>
          {wiki.extract.slice(0, 300)}{wiki.extract.length > 300 ? "…" : ""}
        </div>
      )}

      {node.appSlug && (
        <a
          href={familyAppUrl(node.appSlug)}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "block",
            textAlign: "center",
            padding: "10px 16px",
            background: "#1a1a2a",
            border: "1px solid #2a2a40",
            borderRadius: 8,
            color: "#8899cc",
            textDecoration: "none",
            fontSize: 13,
            fontWeight: 500,
            letterSpacing: "0.02em",
          }}
        >
          Explore {node.commonName ?? node.name} ↗
        </a>
      )}
    </div>
  );
}

export default function InfoPanel({ node, onSelect }: Props) {
  if (!node) return <HomePanel />;
  if (node.rank === "CLASS") return <ClassPanel node={node} onSelect={onSelect} />;
  if (node.rank === "ORDER") return <OrderPanel node={node} onSelect={onSelect} />;
  if (node.rank === "FAMILY") return <FamilyPanel node={node} />;
  return <HomePanel />;
}
