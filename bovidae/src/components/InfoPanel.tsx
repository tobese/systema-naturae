import { useState } from "react";
import type { TaxonNode } from "@shared/types";
import { LINEAGE_COLORS, BREED_GROUP_COLOR } from "../colors";
import { useWikipediaSummary } from "@shared/hooks/useWikipediaSummary";

interface Props {
  node: TaxonNode | null;
  onSelect: (node: TaxonNode) => void;
  findNodeById: (id: string) => TaxonNode | null;
}

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

function collectLeaves(node: TaxonNode): TaxonNode[] {
  if (!node.children || node.children.length === 0) return [node];
  return node.children.flatMap(collectLeaves);
}

function accentFor(node: TaxonNode): string {
  if (node.rank === "FAMILY") return "#F5F5F5";
  if (node.rank === "BREED_GROUP" || node.rank === "BREED") return BREED_GROUP_COLOR;
  if (node.lineage) return LINEAGE_COLORS[node.lineage] ?? "#888";
  return "#888";
}

function LinkRow({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "6px 0",
        borderBottom: "1px solid #1a1a2a",
        color: "#8899bb",
        textDecoration: "none",
        fontSize: 12,
      }}
    >
      <span>{label}</span>
      <span style={{ opacity: 0.5, fontSize: 10 }}>↗</span>
    </a>
  );
}

function ClickableItem({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  const [hover, setHover] = useState(false);
  return (
    <li
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        cursor: "pointer",
        padding: "4px 6px",
        borderRadius: 4,
        marginBottom: 2,
        background: hover ? "rgba(255,255,255,0.05)" : "transparent",
        listStyle: "none",
      }}
    >
      {children}
    </li>
  );
}

function SpeciesPanel({ node, onSelect }: { node: TaxonNode; onSelect: (n: TaxonNode) => void }) {
  const accent = accentFor(node);
  const { data: wiki, loading } = useWikipediaSummary(node.commonName ?? node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;
  const iucnUrl = `https://www.iucnredlist.org/search?query=${encodeURIComponent(node.name)}`;
  const gbifUrl = `https://www.gbif.org/species/search?q=${encodeURIComponent(node.name)}`;
  const subspecies = (node.children ?? []).filter(c => c.rank === "SUBSPECIES");

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Species
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, fontStyle: "italic", marginBottom: 2 }}>
        {node.name}
      </div>
      {node.commonName && (
        <div style={{ fontSize: 16, color: "#aaa", marginBottom: 8 }}>{node.commonName}</div>
      )}
      {node.lineage && (
        <div style={{ fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: "#555" }}>Lineage: </span>
          <span style={{ color: LINEAGE_COLORS[node.lineage] ?? "#aaa" }}>{node.lineage}</span>
        </div>
      )}
      {node.subspeciesCount !== undefined && node.subspeciesCount > 0 && subspecies.length === 0 && (
        <div style={{ fontSize: 13, color: "#666", marginBottom: 4 }}>
          {node.subspeciesCount} subspecies · click to expand
        </div>
      )}
      {node.children && node.children.some(c => c.rank === "BREED_GROUP") && (
        <div style={{ fontSize: 13, color: BREED_GROUP_COLOR, marginBottom: 4 }}>
          {node.children.reduce((s, c) => s + countLeaves(c), 0)} recognised breeds
        </div>
      )}

      {loading && (
        <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />
      )}
      {!loading && wiki?.thumbnail?.source && (
        <img
          src={wiki.thumbnail.source}
          alt={node.commonName ?? node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }}
        />
      )}
      {extract && (
        <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>
      )}

      {subspecies.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>
            Subspecies
          </div>
          <ul style={{ padding: 0, margin: 0 }}>
            {subspecies.map(s => (
              <ClickableItem key={s.id} onClick={() => onSelect(s)}>
                <div style={{ color: "#bbb", fontStyle: "italic", fontSize: 13 }}>{s.name}</div>
                {s.commonName && <div style={{ color: "#666", fontSize: 12 }}>{s.commonName}</div>}
              </ClickableItem>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
          Links
        </div>
        {wikiUrl && <LinkRow href={wikiUrl} label="Wikipedia" />}
        <LinkRow href={iucnUrl} label="IUCN Red List" />
        <LinkRow href={gbifUrl} label="GBIF" />
      </div>
    </div>
  );
}

function SubspeciesPanel({ node }: { node: TaxonNode }) {
  const accent = accentFor(node);
  const { data: wiki, loading } = useWikipediaSummary(node.commonName ?? node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Subspecies
      </div>
      <div style={{ fontSize: 20, fontWeight: 600, color: accent, fontStyle: "italic", marginBottom: 2 }}>
        {node.name}
      </div>
      {node.commonName && (
        <div style={{ fontSize: 15, color: "#aaa", marginBottom: 6 }}>{node.commonName}</div>
      )}

      {loading && (
        <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />
      )}
      {!loading && wiki?.thumbnail?.source && (
        <img
          src={wiki.thumbnail.source}
          alt={node.commonName ?? node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }}
        />
      )}
      {extract && (
        <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>
      )}

      {wikiUrl && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
            Links
          </div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

function BreedPanel({ node }: { node: TaxonNode }) {
  const { data: wiki, loading } = useWikipediaSummary(node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Domestic breed
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: BREED_GROUP_COLOR, marginBottom: 2 }}>
        {node.name}
      </div>
      {node.origin && (
        <div style={{ fontSize: 16, color: "#aaa", marginBottom: 8 }}>{node.origin}</div>
      )}
      {node.lineage && (
        <div style={{ fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: "#555" }}>Lineage: </span>
          <span style={{ color: LINEAGE_COLORS[node.lineage] ?? "#aaa" }}>{node.lineage}</span>
        </div>
      )}

      {loading && (
        <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />
      )}
      {!loading && wiki?.thumbnail?.source && (
        <img
          src={wiki.thumbnail.source}
          alt={node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }}
        />
      )}
      {extract && (
        <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>
      )}

      {wikiUrl && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
            Links
          </div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

function HomePanel() {
  return (
    <div style={{ padding: "24px 20px", color: "#888", fontSize: 13, lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 16 }}>
        Bovidae · Family Tree
      </div>
      <p>Click any node to explore. Click a species with the dashed ring to expand breeds or subspecies.</p>

      <div style={{ marginTop: 28, padding: "12px 14px", borderRadius: 8, background: "#111", fontSize: 12, lineHeight: 1.7 }}>
        <div style={{ color: "#888", marginBottom: 6 }}>Lineages</div>
        {Object.entries(LINEAGE_COLORS).map(([name, color]) => (
          <div key={name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: color }} />
            <span style={{ color: "#ccc" }}>{name}</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 20, padding: "12px 14px", borderRadius: 8, background: "#111", fontSize: 12, lineHeight: 1.7 }}>
        <div style={{ color: "#888", marginBottom: 4 }}>About</div>
        <div style={{ color: "#666" }}>
          Bovidae comprises cattle, buffalo, and bison — the large bovines that have shaped
          human civilisation through meat, milk, leather, and draft power.
          Domestic cattle (<em style={{ color: "#888" }}>Bos taurus</em> and <em style={{ color: "#888" }}>Bos indicus</em>) alone
          number over a billion individuals worldwide.
        </div>
      </div>

      <div style={{ marginTop: 28, fontSize: 11, color: "#444" }}>
        Data: Catalogue of Life ChecklistBank · Breeds: FAO / breed registries
      </div>
    </div>
  );
}

export default function InfoPanel({ node, onSelect, findNodeById: _findNodeById }: Props) {
  if (!node || node.rank === "FAMILY") return <HomePanel />;
  if (node.rank === "SPECIES") return <SpeciesPanel node={node} onSelect={onSelect} />;
  if (node.rank === "SUBSPECIES") return <SubspeciesPanel node={node} />;
  if (node.rank === "BREED") return <BreedPanel node={node} />;

  if (node.rank === "BREED_GROUP") {
    const breeds = collectLeaves(node);
    return (
      <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
          Breed group
        </div>
        <div style={{ fontSize: 22, fontWeight: 600, color: BREED_GROUP_COLOR, marginBottom: 4 }}>{node.name}</div>
        <div style={{ fontSize: 13, color: "#aaa", marginTop: 4 }}>{breeds.length} breeds</div>
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>
            Breeds
          </div>
          <ul style={{ padding: 0, margin: 0 }}>
            {breeds.map(b => (
              <ClickableItem key={b.id} onClick={() => onSelect(b)}>
                <div style={{ color: "#ccc", fontSize: 13 }}>{b.name}</div>
                {b.origin && <div style={{ color: "#555", fontSize: 12 }}>{b.origin}</div>}
              </ClickableItem>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  const accent = accentFor(node);
  const isItalic = node.rank === "GENUS";
  const speciesLeaves = collectLeaves(node).filter(l => l.rank === "SPECIES");
  const leafCount = countLeaves(node);

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        {node.rank.toLowerCase()}
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, fontStyle: isItalic ? "italic" : "normal", marginBottom: 4 }}>
        {node.name}
      </div>
      {node.commonName && (
        <div style={{ fontSize: 15, color: "#aaa", marginBottom: 12 }}>{node.commonName}</div>
      )}
      <div style={{ fontSize: 14, color: "#aaa", marginTop: 8 }}>
        {speciesLeaves.length} species
        {speciesLeaves.length < leafCount && ` · ${leafCount - speciesLeaves.length} breeds`}
      </div>
      {speciesLeaves.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>
            Species
          </div>
          <ul style={{ padding: 0, margin: 0 }}>
            {speciesLeaves.map(s => (
              <ClickableItem key={s.id} onClick={() => onSelect(s)}>
                <div style={{ color: "#bbb", fontStyle: "italic", fontSize: 13 }}>{s.name}</div>
                {s.commonName && <div style={{ color: "#666", fontSize: 12 }}>{s.commonName}</div>}
              </ClickableItem>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
