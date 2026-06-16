import { useState } from "react";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "../types";
import { useWikipediaSummary } from "@shared/hooks/useWikipediaSummary";
import { PORTAL_THEME } from "../colors";
import { COLOR_REGISTRY } from "../colorRegistry";

interface Props {
  node: TaxonNode | null;
  onSelect: (node: TaxonNode) => void;
  findNodeById: (id: string) => TaxonNode | null;
  onFocusFamily: (slug: string | null) => void;
  focusedFamilySlug: string | null;
  subfamilies?: TaxonNode[];
  breadcrumbPath?: TaxonNode[];
}

// Strip parenthetical annotations like "(Älg)" or "(Wapiti)" before Wikipedia lookup
function wikiTitle(commonName: string | undefined, fallback: string): string {
  if (!commonName) return fallback;
  return commonName.replace(/\s*\([^)]*\)/g, "").trim() || fallback;
}

// Natural hybrid notes keyed by species node id (from felidae data)
const NATURAL_HYBRIDS: Record<string, string> = {
  "3DXW2": "Hybridises naturally with domestic cats → Kellas cat (Scotland). Threatens pure wildcat survival.",
  "3DXVF": "Hybridises naturally with domestic cats across Africa and the Middle East.",
  "3WSJW": "Hybridises naturally with Canada lynx where ranges overlap → Blynx.",
  "3WSJS": "Hybridises naturally with bobcat where ranges overlap → Blynx.",
};

const ALWAYS_SKIP_RANKS = new Set(["KINGDOM", "PHYLUM"]);

function countLeaves(node: TaxonNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}
function collectLeaves(node: TaxonNode): TaxonNode[] {
  if (!node.children || node.children.length === 0) return [node];
  return node.children.flatMap(collectLeaves);
}

function accentForNode(node: TaxonNode): string {
  if (node.rank === "FAMILY") return "#F5F5F5";
  if (node.rank === "CLASS") return PORTAL_THEME.lineageColors[node.name] ?? "#C87941";
  if (node.rank === "ORDER") return PORTAL_THEME.lineageColors[node.name] ?? "#8899bb";
  if (node.familySlug) {
    const theme = COLOR_REGISTRY[node.familySlug];
    if (node.rank === "SUBFAMILY" || node.rank === "TRIBE") return theme?.subfamilyColors[node.name] ?? "#888";
    if (node.rank === "BREED_GROUP" || node.rank === "BREED") return theme?.breedGroupColor ?? "#888";
    if (node.rank === "HYBRID" || node.rank === "HYBRID_GROUP") return theme?.hybridColor ?? "#888";
    if (node.lineage) return theme?.lineageColors[node.lineage] ?? "#888";
  }
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

function PanelAncestors({ ancestors, onSelect }: { ancestors: TaxonNode[]; onSelect: (n: TaxonNode) => void }) {
  if (ancestors.length === 0) return null;
  return (
    <div style={{
      display: "flex", flexWrap: "wrap", alignItems: "center", gap: 2,
      marginBottom: 10, fontSize: 10,
    }}>
      {ancestors.map((n, i) => (
        <span key={n.id} style={{ display: "flex", alignItems: "center", gap: 2 }}>
          {i > 0 && <span style={{ color: "#222", userSelect: "none" }}>›</span>}
          <button
            onClick={() => onSelect(n)}
            style={{
              background: "none", border: "none", padding: "1px 3px", borderRadius: 3,
              cursor: "pointer", color: "#3a4a6a", fontSize: 10,
              fontStyle: ["GENUS", "SPECIES", "SUBSPECIES"].includes(n.rank) ? "italic" : "normal",
            }}
            onMouseEnter={e => { e.currentTarget.style.color = "#6688bb"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "#3a4a6a"; }}
          >
            {n.commonName ?? n.name}
          </button>
        </span>
      ))}
    </div>
  );
}

// ─── Portal-level panels ──────────────────────────────────────────────────────

function KingdomPanel({ node, onSelect }: { node: TaxonNode; onSelect: (n: TaxonNode) => void }) {
  const pn = node as PortalNode;
  const phyla = node.children ?? [];
  const classes = phyla.flatMap(p => p.children ?? []);
  return (
    <div style={{ padding: "20px" }}>
      <div style={{ fontSize: 10, color: "#8899bb", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Kingdom</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>{node.commonName ?? node.name}</div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 16 }}>{node.name}</div>
      <div style={{ fontSize: 12, color: "#666", marginBottom: pn.description ? 14 : 20 }}>
        {classes.length} {classes.length === 1 ? "class" : "classes"}
      </div>
      {pn.description && (
        <div style={{ fontSize: 12, color: "#777", lineHeight: 1.7, marginBottom: 20 }}>
          {pn.description}
        </div>
      )}
      <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Classes</div>
      {classes.map(c => (
        <button key={c.id} onClick={() => onSelect(c)} style={{
          display: "block", width: "100%", textAlign: "left",
          background: "none", border: "none", borderBottom: "1px solid #1a1a2a",
          padding: "8px 0", cursor: "pointer", color: "#8899bb", fontSize: 13,
        }}>
          {c.commonName ?? c.name}
          <span style={{ float: "right", color: "#333", fontSize: 11 }}>
            {(c.children ?? []).length} {(c.children ?? []).length === 1 ? "order" : "orders"}
          </span>
        </button>
      ))}
    </div>
  );
}

function OverviewHomePanel({ onFocusFamily }: { onFocusFamily: (slug: string | null) => void }) {
  void onFocusFamily;
  return (
    <div style={{ padding: "24px 20px", color: "#555" }}>
      <div style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 20 }}>
        Explore the animal kingdom. Click any{" "}
        <span style={{ color: "#e0e0e0", fontWeight: 500 }}>family node</span>{" "}
        in the tree to expand its full species tree in place.
      </div>
      <div style={{ fontSize: 11, color: "#3a3a4a", lineHeight: 1.6 }}>
        <div style={{ marginBottom: 6 }}>White nodes → clickable family entries</div>
        <div style={{ marginBottom: 6 }}>Amber nodes → Mammalia orders</div>
        <div style={{ marginBottom: 6 }}>Teal nodes → Aves orders</div>
        <div style={{ marginBottom: 6 }}>Esc or ← All families → collapse family</div>
      </div>
    </div>
  );
}

function ClassPanel({ node, onSelect }: { node: TaxonNode; onSelect: (n: TaxonNode) => void }) {
  const accent = accentForNode(node);
  const orders = node.children ?? [];
  const families = orders.flatMap(o => o.children ?? []) as PortalNode[];
  return (
    <div style={{ padding: "20px" }}>
      <div style={{ fontSize: 10, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Class</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>{node.commonName ?? node.name}</div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 16 }}>{node.name}</div>
      <div style={{ fontSize: 12, color: "#666", marginBottom: (node as PortalNode).description ? 14 : 20 }}>
        {orders.length} {orders.length === 1 ? "order" : "orders"} · {families.length} {families.length === 1 ? "family" : "families"}
      </div>
      {(node as PortalNode).description && (
        <div style={{ fontSize: 12, color: "#777", lineHeight: 1.7, marginBottom: 20 }}>
          {(node as PortalNode).description}
        </div>
      )}
      <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Orders</div>
      {orders.map(o => (
        <button key={o.id} onClick={() => onSelect(o)} style={{
          display: "block", width: "100%", textAlign: "left",
          background: "none", border: "none", borderBottom: "1px solid #1a1a2a",
          padding: "8px 0", cursor: "pointer", color: "#8899bb", fontSize: 13,
        }}>
          {o.commonName ?? o.name}
          <span style={{ float: "right", color: "#333", fontSize: 11 }}>
            {(o.children ?? []).length} {(o.children ?? []).length === 1 ? "family" : "families"}
          </span>
        </button>
      ))}
    </div>
  );
}

function OrderPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const families = (node.children ?? []) as PortalNode[];
  return (
    <div style={{ padding: "20px" }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 10, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Order</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>{node.commonName ?? node.name}</div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 16 }}>{node.name}</div>
      <div style={{ fontSize: 12, color: "#666", marginBottom: (node as PortalNode).description ? 14 : 20 }}>
        {families.length} {families.length === 1 ? "family" : "families"}
      </div>
      {(node as PortalNode).description && (
        <div style={{ fontSize: 12, color: "#777", lineHeight: 1.7, marginBottom: 20 }}>
          {(node as PortalNode).description}
        </div>
      )}
      <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Families</div>
      {families.map(f => (
        <button key={f.id} onClick={() => onSelect(f)} style={{
          display: "block", width: "100%", textAlign: "left",
          background: "none", border: "none", borderBottom: "1px solid #1a1a2a",
          padding: "8px 0", cursor: "pointer", color: "#8899bb", fontSize: 13,
        }}>
          {f.commonName ?? f.name}
          <span style={{ float: "right", color: "#333", fontSize: 11 }}>{f.speciesCount} spp.</span>
        </button>
      ))}
    </div>
  );
}

function FamilyPanel({ node, onFocusFamily, focusedFamilySlug, ancestors, onSelect }: {
  node: TaxonNode;
  onFocusFamily: (slug: string | null) => void;
  focusedFamilySlug: string | null;
  ancestors: TaxonNode[];
  onSelect: (n: TaxonNode) => void;
}) {
  const pn = node as PortalNode;
  const { data: wiki } = useWikipediaSummary(node.name); // use scientific name — common names with & don't map to Wikipedia
  const isFocused = pn.appSlug === focusedFamilySlug;

  return (
    <div style={{ padding: "20px" }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 10, color: "#F5F5F5", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Family</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 2 }}>{node.commonName ?? node.name}</div>
      <div style={{ fontSize: 12, color: "#555", fontStyle: "italic", marginBottom: 4 }}>{node.name}</div>
      {pn.speciesCount !== undefined && (
        <div style={{ fontSize: 12, color: "#666", marginBottom: 16 }}>{pn.speciesCount} species</div>
      )}
      {pn.taxonomicNote && (
        <div style={{
          fontSize: 11, color: "#555", fontStyle: "italic",
          background: "#0a0a14", border: "1px solid #1a1a2a", borderRadius: 6,
          padding: "8px 10px", marginBottom: 16, lineHeight: 1.5,
        }}>
          {pn.taxonomicNote}
        </div>
      )}
      {pn.notableMembers && pn.notableMembers.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: "#444", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
            Notable members
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {pn.notableMembers.map(m => (
              <span key={m} style={{
                fontSize: 11, color: "#7788aa", background: "#0d0d1a",
                border: "1px solid #1e2030", borderRadius: 4, padding: "3px 8px",
              }}>
                {m}
              </span>
            ))}
          </div>
        </div>
      )}
      {wiki?.extract && (
        <div style={{ fontSize: 12, color: "#666", lineHeight: 1.7, marginBottom: 20 }}>
          {wiki.extract.slice(0, 320)}{wiki.extract.length > 320 ? "…" : ""}
        </div>
      )}
      {pn.appSlug && (
        <button
          onClick={() => onFocusFamily(isFocused ? null : (pn.appSlug ?? null))}
          style={{
            display: "block", width: "100%", textAlign: "center",
            padding: "10px 16px", borderRadius: 8, cursor: "pointer",
            background: isFocused ? "#1a2a3a" : "#1a1a2a",
            border: `1px solid ${isFocused ? "#3a5a7a" : "#2a2a40"}`,
            color: isFocused ? "#6aafee" : "#8899cc",
            fontSize: 13, fontWeight: 500, letterSpacing: "0.02em",
          }}
        >
          {isFocused ? "← Collapse species tree" : `Expand ${node.commonName ?? node.name} in tree`}
        </button>
      )}
    </div>
  );
}

// ─── Family-level panels ──────────────────────────────────────────────────────

function FamilyHomePanel({ subfamilies, onSelect, focusedFamilySlug }: {
  subfamilies: TaxonNode[];
  onSelect: (n: TaxonNode) => void;
  focusedFamilySlug: string | null;
}) {
  const theme = focusedFamilySlug ? COLOR_REGISTRY[focusedFamilySlug] : null;
  return (
    <div style={{ padding: "24px 20px", color: "#888", fontSize: 13, lineHeight: 1.6 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 16 }}>
        Click any node to explore.
      </div>
      {subfamilies.length > 0 && theme && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>Subfamilies</div>
          {subfamilies.map(sf => (
            <button key={sf.id} onClick={() => onSelect(sf)} style={{
              display: "block", width: "100%", textAlign: "left",
              background: "none", border: "none", borderBottom: "1px solid #1a1a2a",
              padding: "7px 0", cursor: "pointer",
              color: theme.subfamilyColors[sf.name] ?? "#8899bb", fontSize: 13,
            }}>
              {sf.commonName ?? sf.name}
              <span style={{ float: "right", color: "#333", fontSize: 11 }}>{countLeaves(sf)} spp.</span>
            </button>
          ))}
        </div>
      )}
      {theme && Object.keys(theme.lineageColors).length > 0 && (
        <div style={{ padding: "12px 14px", borderRadius: 8, background: "#111", fontSize: 12, lineHeight: 1.7 }}>
          <div style={{ color: "#888", marginBottom: 6 }}>Lineage colours</div>
          {Object.entries(theme.lineageColors).map(([name, color]) => (
            <div key={name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
              <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: color }} />
              <span style={{ color: "#ccc" }}>{name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SubfamilyPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const species = collectLeaves(node).filter(l => l.rank === "SPECIES");
  const genera = (node.children ?? []).filter(c => c.rank === "GENUS");
  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        {node.rank.toLowerCase()}
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, marginBottom: 4 }}>{node.name}</div>
      {node.commonName && <div style={{ fontSize: 15, color: "#aaa", marginBottom: 12 }}>{node.commonName}</div>}
      <div style={{ fontSize: 13, color: "#666", marginBottom: genera.length > 0 ? 20 : 0 }}>{species.length} species</div>
      {genera.length > 0 && (
        <>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>Genera</div>
          <ul style={{ padding: 0, margin: 0 }}>
            {genera.map(g => (
              <ClickableItem key={g.id} onClick={() => onSelect(g)}>
                <div style={{ color: "#bbb", fontStyle: "italic", fontSize: 13 }}>{g.name}</div>
                <div style={{ color: "#666", fontSize: 12 }}>{collectLeaves(g).filter(l => l.rank === "SPECIES").length} spp.</div>
              </ClickableItem>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function GenusPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const species = collectLeaves(node).filter(l => l.rank === "SPECIES");
  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Genus</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, fontStyle: "italic", marginBottom: 4 }}>{node.name}</div>
      {node.commonName && <div style={{ fontSize: 14, color: "#aaa", marginBottom: 8 }}>{node.commonName}</div>}
      {node.description && (
        <div style={{ fontSize: 13, color: "#777", lineHeight: 1.7, marginBottom: 14 }}>{node.description}</div>
      )}
      <div style={{ fontSize: 13, color: "#666", marginBottom: 16 }}>{species.length} {species.length === 1 ? "species" : "species"}</div>
      {species.length > 0 && (
        <>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>Species</div>
          <ul style={{ padding: 0, margin: 0 }}>
            {species.map(s => (
              <ClickableItem key={s.id} onClick={() => onSelect(s)}>
                <div style={{ color: "#bbb", fontStyle: "italic", fontSize: 13 }}>{s.name}</div>
                {s.commonName && <div style={{ color: "#666", fontSize: 12 }}>{s.commonName}</div>}
              </ClickableItem>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function SpeciesPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const { data: wiki, loading } = useWikipediaSummary(wikiTitle(node.commonName, node.name));
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;
  const iucnUrl = `https://www.iucnredlist.org/search?query=${encodeURIComponent(node.name)}`;
  const gbifUrl = `https://www.gbif.org/species/search?q=${encodeURIComponent(node.name)}`;
  const colUrl = `https://www.checklistbank.org/dataset/3LR/taxon/${node.id}`;

  const subspecies = (node.children ?? []).filter(c => c.rank === "SUBSPECIES");
  const breedGroups = (node.children ?? []).filter(c => c.rank === "BREED_GROUP");

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Species</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, fontStyle: "italic", marginBottom: 2 }}>{node.name}</div>
      {node.commonName && <div style={{ fontSize: 16, color: "#aaa", marginBottom: 8 }}>{node.commonName}</div>}
      {node.lineage && (
        <div style={{ fontSize: 13, marginBottom: 4 }}>
          <span style={{ color: "#555" }}>Lineage: </span>
          <span style={{ color: accent }}>{node.lineage}</span>
        </div>
      )}
      {(node.subspeciesCount ?? 0) > 0 && subspecies.length === 0 && (
        <div style={{ fontSize: 13, color: "#666", marginBottom: 4 }}>
          {node.subspeciesCount} subspecies · click to expand
        </div>
      )}
      {breedGroups.length === 0 && !node.children?.length && (node.subspeciesCount ?? 0) === 0 && null}

      {loading && <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />}
      {!loading && wiki?.thumbnail?.source && (
        <img src={wiki.thumbnail.source} alt={node.commonName ?? node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }} />
      )}
      {extract && <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>}

      {/* Breed groups */}
      {breedGroups.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>
            Breeds · {breedGroups.reduce((s, bg) => s + countLeaves(bg), 0)} recognized
          </div>
          <ul style={{ padding: 0, margin: 0 }}>
            {breedGroups.map(bg => (
              <ClickableItem key={bg.id} onClick={() => onSelect(bg)}>
                <div style={{ color: "#ccc", fontSize: 13 }}>{bg.name}</div>
                <div style={{ color: "#555", fontSize: 12 }}>{countLeaves(bg)} breeds</div>
              </ClickableItem>
            ))}
          </ul>
        </div>
      )}

      {/* Subspecies */}
      {subspecies.length > 0 && (() => {
        const accepted = subspecies.filter(s => s.accepted !== false);
        const synonyms = subspecies.filter(s => s.accepted === false);
        return (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#555", marginBottom: 8 }}>Subspecies</div>
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

      {NATURAL_HYBRIDS[node.id] && (
        <div style={{ fontSize: 12, color: "#8899bb", marginTop: 14, padding: "8px 10px", background: "#111820", borderRadius: 6, lineHeight: 1.5 }}>
          <span style={{ color: "#556" }}>Natural hybrid: </span>{NATURAL_HYBRIDS[node.id]}
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>Links</div>
        {wikiUrl && <LinkRow href={wikiUrl} label="Wikipedia" />}
        <LinkRow href={colUrl} label="COL ChecklistBank" />
        <LinkRow href={iucnUrl} label="IUCN Red List" />
        <LinkRow href={gbifUrl} label="GBIF" />
      </div>
    </div>
  );
}

function SubspeciesPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const { data: wiki, loading } = useWikipediaSummary(wikiTitle(node.commonName, node.name));
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Subspecies</div>
      <div style={{ fontSize: 20, fontWeight: 600, color: node.accepted === false ? "#666" : accent, fontStyle: "italic", marginBottom: 2 }}>
        {node.name}
      </div>
      {node.commonName && <div style={{ fontSize: 15, color: node.accepted === false ? "#666" : "#aaa", marginBottom: 6 }}>{node.commonName}</div>}
      {node.accepted === false && (
        <div style={{ fontSize: 11, color: "#4a4a66", padding: "4px 8px", background: "#111118", borderRadius: 4, marginBottom: 8, lineHeight: 1.5 }}>
          Not recognized as a distinct subspecies by COL taxonomy
        </div>
      )}
      {loading && <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />}
      {!loading && wiki?.thumbnail?.source && (
        <img src={wiki.thumbnail.source} alt={node.commonName ?? node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }} />
      )}
      {extract && <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>}
      {wikiUrl && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>Links</div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

function BreedGroupPanel({ node, onSelect, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; ancestors: TaxonNode[] }) {
  const accent = accentForNode(node);
  const breeds = collectLeaves(node);
  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>
        Breed group
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, marginBottom: 4 }}>{node.name}</div>
      <div style={{ fontSize: 13, color: "#aaa", marginTop: 4, marginBottom: 16 }}>{breeds.length} breeds</div>
      <ul style={{ padding: 0, margin: 0 }}>
        {breeds.map(b => (
          <ClickableItem key={b.id} onClick={() => onSelect(b)}>
            <div style={{ color: "#ccc", fontSize: 13 }}>{b.name}</div>
            {b.origin && <div style={{ color: "#555", fontSize: 12 }}>{b.origin}</div>}
          </ClickableItem>
        ))}
      </ul>
    </div>
  );
}

function BreedPanel({ node, onSelect, findNodeById, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; findNodeById: (id: string) => TaxonNode | null; ancestors: TaxonNode[] }) {
  const theme = node.familySlug ? COLOR_REGISTRY[node.familySlug] : null;
  const accent = theme?.breedGroupColor ?? "#888";
  const coatAccent = theme?.coatTypeColor ?? "#5DB8C4";
  const { data: wiki, loading } = useWikipediaSummary(node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Domestic breed</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, marginBottom: 2 }}>{node.name}</div>
      {node.origin && <div style={{ fontSize: 16, color: "#aaa", marginBottom: 4 }}>{node.origin}</div>}
      {node.coatType && (
        <div style={{ fontSize: 13, color: "#aaa", marginBottom: 8 }}>
          <span style={{ color: "#555" }}>Coat: </span>
          {node.coatType}
          {node.coatType === "rex" && (
            <span style={{ color: coatAccent, marginLeft: 8, fontSize: 12 }}>↔ connected in tree</span>
          )}
        </div>
      )}
      {loading && <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />}
      {!loading && wiki?.thumbnail?.source && (
        <img src={wiki.thumbnail.source} alt={node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }} />
      )}
      {extract && <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>}
      {node.wildParentId && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 6 }}>Wild origin</div>
          <button
            onClick={() => { const p = findNodeById(node.wildParentId!); if (p) onSelect(p); }}
            style={{
              display: "block", width: "100%", textAlign: "left",
              background: "none", border: "1px solid #1e2030", borderRadius: 6,
              padding: "7px 10px", cursor: "pointer", color: "#bbb", fontSize: 13, fontStyle: "italic",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = accent; e.currentTarget.style.color = "#fff"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e2030"; e.currentTarget.style.color = "#bbb"; }}
          >
            {node.wildParentName ?? node.wildParentId}
          </button>
        </div>
      )}
      {wikiUrl && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>Links</div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

function HybridPanel({ node, onSelect, findNodeById, ancestors }: { node: TaxonNode; onSelect: (n: TaxonNode) => void; findNodeById: (id: string) => TaxonNode | null; ancestors: TaxonNode[] }) {
  const theme = node.familySlug ? COLOR_REGISTRY[node.familySlug] : null;
  const accent = theme?.hybridColor ?? "#C8A050";
  const { data: wiki, loading } = useWikipediaSummary(node.name);
  const extract = wiki?.extract ?? null;
  const wikiUrl = wiki?.content_urls?.desktop?.page;
  const parents = (node.hybridParents ?? []).map(id => findNodeById(id)).filter(Boolean) as TaxonNode[];

  return (
    <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
      <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
      <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Hybrid</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: accent, marginBottom: 2 }}>{node.name}</div>
      {node.lineage && <div style={{ fontSize: 14, color: "#aaa", marginBottom: 8 }}>{node.lineage}</div>}
      {loading && <div style={{ marginTop: 16, width: "100%", height: 120, background: "#1a1a2a", borderRadius: 6 }} />}
      {!loading && wiki?.thumbnail?.source && (
        <img src={wiki.thumbnail.source} alt={node.name}
          style={{ marginTop: 16, width: "100%", height: "auto", borderRadius: 6, display: "block" }} />
      )}
      {extract && <p style={{ fontSize: 14, color: "#999", marginTop: 12, lineHeight: 1.65 }}>{extract}</p>}
      {parents.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 8 }}>Parent species</div>
          {parents.map(p => (
            <button key={p.id} onClick={() => onSelect(p)} style={{
              display: "block", width: "100%", textAlign: "left",
              background: "none", border: "1px solid #1e2030", borderRadius: 6,
              padding: "7px 10px", marginBottom: 6, cursor: "pointer",
              color: "#bbb", fontSize: 13, fontStyle: "italic",
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = accent; e.currentTarget.style.color = "#fff"; }}
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
          <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>Links</div>
          <LinkRow href={wikiUrl} label="Wikipedia" />
        </div>
      )}
    </div>
  );
}

// ─── Main dispatch ────────────────────────────────────────────────────────────

export default function UnifiedInfoPanel({
  node,
  onSelect,
  findNodeById,
  onFocusFamily,
  focusedFamilySlug,
  subfamilies = [],
  breadcrumbPath = [],
}: Props) {
  if (!node) {
    return focusedFamilySlug
      ? <FamilyHomePanel subfamilies={subfamilies} onSelect={onSelect} focusedFamilySlug={focusedFamilySlug} />
      : <OverviewHomePanel onFocusFamily={onFocusFamily} />;
  }

  // Compute ancestors: full path minus current node, filtering out meaningless ranks.
  // When a family is focused, also skip CLASS and ORDER — the family context is shown in the header.
  const ancestors = breadcrumbPath
    .filter(n => !ALWAYS_SKIP_RANKS.has(n.rank))
    .slice(0, -1); // remove the current node itself

  // Portal-level
  if (node.rank === "KINGDOM") return <KingdomPanel node={node} onSelect={onSelect} />;
  if (node.rank === "PHYLUM") return null;
  if (node.rank === "CLASS") return <ClassPanel node={node} onSelect={onSelect} />;
  if (node.rank === "ORDER") return <OrderPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "FAMILY") {
    return <FamilyPanel node={node} onFocusFamily={onFocusFamily} focusedFamilySlug={focusedFamilySlug} ancestors={ancestors} onSelect={onSelect} />;
  }

  // Family-level
  if (node.rank === "SUBFAMILY" || node.rank === "TRIBE")
    return <SubfamilyPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "GENUS") return <GenusPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "SPECIES") return <SpeciesPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "SUBSPECIES") return <SubspeciesPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "BREED_GROUP") return <BreedGroupPanel node={node} onSelect={onSelect} ancestors={ancestors} />;
  if (node.rank === "BREED") return <BreedPanel node={node} onSelect={onSelect} findNodeById={findNodeById} ancestors={ancestors} />;
  if (node.rank === "HYBRID_GROUP") {
    const hybrids = node.children ?? [];
    const theme = node.familySlug ? COLOR_REGISTRY[node.familySlug] : null;
    const accent = theme?.hybridColor ?? "#C8A050";
    return (
      <div style={{ padding: "24px 20px", lineHeight: 1.6 }}>
        <PanelAncestors ancestors={ancestors} onSelect={onSelect} />
        <div style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "#555", marginBottom: 10 }}>Hybrids</div>
        <div style={{ fontSize: 22, fontWeight: 600, color: accent, marginBottom: 4 }}>Hybrids</div>
        <div style={{ fontSize: 13, color: "#aaa", marginTop: 4 }}>{hybrids.length} documented interspecies hybrids</div>
        <ul style={{ padding: 0, margin: 0, marginTop: 20 }}>
          {hybrids.map(h => (
            <ClickableItem key={h.id} onClick={() => onSelect(h)}>
              <div style={{ color: accent, fontSize: 13, fontWeight: 600 }}>{h.name}</div>
              {h.lineage && <div style={{ color: "#666", fontSize: 12 }}>{h.lineage}</div>}
            </ClickableItem>
          ))}
        </ul>
        <div style={{ marginTop: 20, fontSize: 12, color: "#555", lineHeight: 1.6 }}>
          Interspecies hybrids exist only in captivity. Dashed lines connect each hybrid to its parent species.
        </div>
      </div>
    );
  }
  if (node.rank === "HYBRID") return <HybridPanel node={node} onSelect={onSelect} findNodeById={findNodeById} ancestors={ancestors} />;

  return null;
}
