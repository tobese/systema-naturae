import { useState } from "react";
import type { TaxonNode } from "@shared/types";
import { LINEAGE_COLORS, BREED_GROUP_COLOR, HYBRID_COLOR } from "../colors";
import { useWikipediaSummary } from "@shared/hooks/useWikipediaSummary";

interface Props {
  node: TaxonNode | null;
  onSelect: (node: TaxonNode) => void;
  findNodeById: (id: string) => TaxonNode | null;
  subfamilies?: TaxonNode[];
}

const NATURAL_HYBRIDS: Record<string, string> = {
  "Equus przewalskii": "Closely related to the domestic horse; captive crosses with E. asinus produce mule-like hybrids.",
  "Equus asinus":      "Domestic donkeys cross with horses to produce mules (♂ donkey × ♀ horse) and hinnies (♂ horse × ♀ donkey).",
  "Equus africanus":   "Wild ancestor of the domestic donkey; hybridises occasionally with onagers in Asia.",
  "Equus quagga":      "Occasionally crosses with horses (zorse) or donkeys (zedonk) in captivity.",
};

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

function ClickableItem({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick: () => void;
}) {
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
  const subspecies = (node.children ?? []).filter(c => c.rank === "SUBSPECIES");

  const wikiUrl = wiki?.content_urls?.desktop?.page;
  const colUrl = `https://www.checklistbank.org/dataset/3LR/taxon/${node.id}`;
  const iucnUrl = `https://www.iucnredlist.org/search?query=${encodeURIComponent(node.name)}`;
  const gbifUrl = `https://www.gbif.org/species/search?q=${encodeURIComponent(node.name)}`;

  const naturalHybridNote = NATURAL_HYBRIDS[node.name];

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

      {subspecies.length > 0 && (() => {
        const accepted = subspecies.filter(s => s.accepted !== false);
        const synonyms = subspecies.filter(s => s.accepted === false);
        return (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>
              Subspecies
            </div>
            <ul style={{ padding: 0, margin: 0 }}>
              {accepted.map(s => (
                <ClickableItem key={s.id} onClick={() => onSelect(s)}>
                  <div style={{ color: "#bbb", fontStyle: "italic", fontSize: 13 }}>{s.name}</div>
                  {s.commonName && <div style={{ color: "#666", fontSize: 12 }}>{s.commonName}</div>}
                </ClickableItem>
              ))}
            </ul>
            {synonyms.length > 0 && (
              <>
                <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#3d3d55", marginTop: 10, marginBottom: 6 }}>
                  Historical / not COL-accepted
                </div>
                <ul style={{ padding: 0, margin: 0 }}>
                  {synonyms.map(s => (
                    <ClickableItem key={s.id} onClick={() => onSelect(s)}>
                      <div style={{ color: "#777", fontStyle: "italic", fontSize: 13 }}>{s.name}</div>
                      {s.commonName && <div style={{ color: "#4a4a66", fontSize: 12 }}>{s.commonName}</div>}
                    </ClickableItem>
                  ))}
                </ul>
              </>
            )}
          </div>
        );
      })()}

      {naturalHybridNote && (
        <div style={{ fontSize: 12, color: "#8899bb", marginTop: 14, padding: "8px 10px", background: "#111820", borderRadius: 6, lineHeight: 1.5 }}>
          <span style={{ color: "#556" }}>Natural hybrid: </span>{naturalHybridNote}
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
          Links
        </div>
        {wikiUrl && <LinkRow href={wikiUrl} label="Wikipedia" />}
        <LinkRow href={colUrl} label="COL ChecklistBank" />
        <LinkRow href={iucnUrl} label="IUCN Red List" />
        <LinkRow href={gbifUrl} label="GBIF" />
      </div>
    </div>
  );
}

function HybridPanel({ node, onSelect, findNodeById }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; findNodeById: (id: string) => TaxonNode | null }) {
  const { data: wiki, loading } = useWikipediaSummary(node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;
  const parents = (node.hybridParents ?? []).map(id => findNodeById(id)).filter(Boolean) as TaxonNode[];

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Hybrid
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: HYBRID_COLOR, marginBottom: 2 }}>
        {node.name}
      </div>
      {node.lineage && (
        <div style={{ fontSize: 14, color: "#aaa", marginBottom: 8 }}>{node.lineage}</div>
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

      {parents.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 8 }}>
            Parent species
          </div>
          {parents.map(p => (
            <button
              key={p.id}
              onClick={() => onSelect(p)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                background: "none",
                border: "1px solid #1e2030",
                borderRadius: 6,
                padding: "7px 10px",
                marginBottom: 6,
                cursor: "pointer",
                color: "#bbb",
                fontSize: 13,
                fontStyle: "italic",
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = HYBRID_COLOR; e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e2030"; e.currentTarget.style.color = "#bbb"; }}
            >
              {p.name}
              {p.commonName && <span style={{ fontStyle: "normal", color: "#666", marginLeft: 8, fontSize: 12 }}>{p.commonName}</span>}
            </button>
          ))}
        </div>
      )}

      {wikiUrl && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
            Links
          </div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

function SubspeciesPanel({ node }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; findNodeById: (id: string) => TaxonNode | null }) {
  const accent = accentFor(node);
  const { data: wiki, loading } = useWikipediaSummary(node.commonName ?? node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Subspecies
      </div>
      <div style={{ fontSize: 20, fontWeight: 600, color: node.accepted === false ? "#666" : accent, fontStyle: "italic", marginBottom: 2 }}>
        {node.name}
      </div>
      {node.commonName && (
        <div style={{ fontSize: 15, color: node.accepted === false ? "#666" : "#aaa", marginBottom: 6 }}>{node.commonName}</div>
      )}
      {node.accepted === false && (
        <div style={{ fontSize: 11, color: "#4a4a66", padding: "4px 8px", background: "#111118", borderRadius: 4, marginBottom: 8, lineHeight: 1.5 }}>
          Not recognised as a distinct subspecies by COL taxonomy
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

function BreedPanel({ node }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; findNodeById: (id: string) => TaxonNode | null }) {
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

      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>
          Links
        </div>
        {wikiUrl && <LinkRow href={wikiUrl} label="Wikipedia" />}
        <LinkRow href="https://en.wikipedia.org/wiki/Horse" label="Domestic Horse (Wikipedia)" />
      </div>
    </div>
  );
}

function HomePanel({ onSelect: _onSelect }: { subfamilies: TaxonNode[]; onSelect: (n: TaxonNode) => void }) {
  return (
    <div style={{ padding: "24px 20px", color: "#888", fontSize: 13, lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 16 }}>
        Equidae · Family Tree
      </div>
      <p>Click any node to explore. Click a species with the dashed ring to expand subspecies.</p>

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
          All living equids belong to the single genus <em style={{ color: "#888" }}>Equus</em>.
          Horses, asses, and zebras diverged ~4 million years ago and can still
          produce fertile-to-sterile offspring across species — making equid
          hybrids some of the most historically significant animals in human civilisation.
        </div>
      </div>

      <div style={{ marginTop: 28, fontSize: 11, color: "#444" }}>
        Data: Catalogue of Life ChecklistBank · Breeds: FEI / breed registries
      </div>
    </div>
  );
}

export default function InfoPanel({ node, onSelect, findNodeById, subfamilies = [] }: Props) {
  if (!node || node.rank === "FAMILY") {
    return <HomePanel subfamilies={subfamilies} onSelect={onSelect} />;
  }

  if (node.rank === "SPECIES") return <SpeciesPanel node={node} onSelect={onSelect} />;
  if (node.rank === "SUBSPECIES") return <SubspeciesPanel node={node} onSelect={onSelect} findNodeById={findNodeById} />;
  if (node.rank === "BREED") return <BreedPanel node={node} onSelect={onSelect} findNodeById={findNodeById} />;
  if (node.rank === "HYBRID") return <HybridPanel node={node} onSelect={onSelect} findNodeById={findNodeById} />;
  if (node.rank === "HYBRID_GROUP") {
    const hybrids = node.children ?? [];
    return (
      <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
          Hybrids
        </div>
        <div style={{ fontSize: 22, fontWeight: 600, color: HYBRID_COLOR, marginBottom: 4 }}>Hybrids</div>
        <div style={{ fontSize: 13, color: "#aaa", marginTop: 4 }}>{hybrids.length} documented interspecies hybrids</div>
        <div style={{ marginTop: 20 }}>
          <ul style={{ padding: 0, margin: 0 }}>
            {hybrids.map(h => (
              <ClickableItem key={h.id} onClick={() => onSelect(h)}>
                <div style={{ color: HYBRID_COLOR, fontSize: 13, fontWeight: 600 }}>{h.name}</div>
                {h.lineage && <div style={{ color: "#666", fontSize: 12 }}>{h.lineage}</div>}
              </ClickableItem>
            ))}
          </ul>
        </div>
        <div style={{ marginTop: 20, fontSize: 12, color: "#555", lineHeight: 1.6 }}>
          Equid hybrids occur in captivity; mules are bred deliberately worldwide and have been
          central to agriculture and transport for thousands of years.
        </div>
      </div>
    );
  }

  if (node.rank === "BREED_GROUP") {
    const breeds = collectLeaves(node);
    return (
      <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
          Discipline group
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

  const leafCount = countLeaves(node);
  const directChildren = node.children ?? [];
  const speciesLeaves = collectLeaves(node).filter(l => l.rank === "SPECIES");

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
        {speciesLeaves.length} {speciesLeaves.length === 1 ? "species" : "species"}
        {speciesLeaves.length < leafCount && ` · ${leafCount - speciesLeaves.length} breeds`}
      </div>

      {directChildren.length > 0 && (
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
