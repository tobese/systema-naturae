import { useEffect, useMemo, useRef, useState } from "react";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "../types";
import ImportTimeline from "./ImportTimeline";
import importLog from "../../data/import-log.json";

interface Props {
  data: TaxonNode;
  onClose: () => void;
  onFocusFamily: (slug: string) => void;
  initialFamilySlug?: string | null;
  initialClassId?: string | null;
}

interface CoverageNode {
  id: string;
  name: string;
  commonName?: string;
  rank: string;
  appSlug?: string;
  portalCount: number;
  totalCount?: number;
  children?: CoverageNode[];
}

interface ClassCoverage {
  id: string;
  name: string;
  commonName?: string;
  families: CoverageNode[];
}

function countSpecies(node: TaxonNode): number {
  if (node.rank === "SPECIES") return 1;
  return (node.children ?? []).reduce((sum, c) => sum + countSpecies(c), 0);
}

function buildCoverageTree(node: TaxonNode): CoverageNode | null {
  if (node.rank === "SPECIES" || node.rank === "SUBSPECIES") return null;
  const pn = node as PortalNode;
  const cn: CoverageNode = {
    id: node.id, name: node.name, commonName: node.commonName,
    rank: node.rank, appSlug: pn.appSlug,
    portalCount: countSpecies(node), totalCount: pn.speciesCount,
  };
  const children = (node.children ?? []).map(buildCoverageTree).filter((c): c is CoverageNode => c !== null);
  if (children.length > 0 && (cn.totalCount !== undefined || children.some(c => c.totalCount !== undefined))) {
    cn.children = children;
  }
  return cn;
}

function buildCoverage(root: TaxonNode): ClassCoverage[] {
  const classes: ClassCoverage[] = [];
  const other: ClassCoverage = { id: "__other__", name: "Other", families: [] };
  function walk(node: TaxonNode, currentClass: ClassCoverage | null) {
    if (node.rank === "CLASS") {
      const cls: ClassCoverage = { id: node.id, name: node.name, commonName: node.commonName, families: [] };
      classes.push(cls);
      (node.children ?? []).forEach(c => walk(c, cls)); return;
    }
    if (node.rank === "FAMILY") {
      const tree = buildCoverageTree(node);
      if (tree) (currentClass ?? other).families.push(tree); return;
    }
    (node.children ?? []).forEach(c => walk(c, currentClass));
  }
  walk(root, null);
  if (other.families.length > 0) classes.push(other);
  return classes;
}

type SortMode = "gaps" | "az";
type FilterMode = "all" | "complete" | "partial" | "gaps";

function statusText(pc: number, tc?: number): string {
  if (pc === 0) return "·";
  if (tc !== undefined && pc >= tc) return "✓";
  return `-${((tc ?? pc) - pc).toLocaleString()}`;
}

function tagColor(pc: number, tc?: number): string {
  if (pc === 0) return "#444";
  if (tc !== undefined && pc >= tc) return "#44aa66";
  return "#cc9944";
}

/** Class-level traffic sign: green/all done, amber/mixed, red/all gapped */
function classTraffic(families: CoverageNode[]): "green" | "amber" | "red" {
  let hasComplete = false, hasGap = false;
  for (const f of families) {
    if (f.totalCount === undefined || f.totalCount === 0) continue;
    if (f.portalCount >= f.totalCount) hasComplete = true;
    else hasGap = true;
  }
  if (hasComplete && !hasGap) return "green";
  if (hasComplete || hasGap) return "amber";
  return "red";
}

const TRAFFIC_COLORS = { green: "#44aa66", amber: "#cc9944", red: "#d84848" };

export default function CoverageModal({ data, onClose, onFocusFamily, initialFamilySlug, initialClassId }: Props) {
  const [tab, setTab] = useState<"coverage" | "growth">("coverage");
  const [sort, setSort] = useState<SortMode>("gaps");
  const [filter, setFilter] = useState<FilterMode>("all");
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const targetRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const classes = useMemo(() => buildCoverage(data), [data]);
  const totalFamilies = useMemo(() => classes.reduce((sum, cls) => sum + cls.families.length, 0), [classes]);

  function toggleClass(id: string) {
    setCollapsed(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  const allCollapsed = classes.length > 0 && classes.every(c => collapsed.has(c.id));

  function toggleAll() {
    if (allCollapsed) {
      setCollapsed(new Set());
    } else {
      setCollapsed(new Set(classes.map(c => c.id)));
    }
  }

  function sortedFamilies(families: CoverageNode[]): CoverageNode[] {
    let sorted = [...families];
    if (sort === "gaps") {
      sorted.sort((a, b) => {
        const ga = a.totalCount !== undefined ? a.totalCount - a.portalCount : Infinity;
        const gb = b.totalCount !== undefined ? b.totalCount - b.portalCount : Infinity;
        return gb - ga;
      });
    } else {
      sorted.sort((a, b) => (a.commonName ?? a.name).localeCompare(b.commonName ?? b.name));
    }
    if (filter === "complete") return sorted.filter(f => f.totalCount !== undefined && f.portalCount >= f.totalCount);
    if (filter === "partial") return sorted.filter(f => f.totalCount !== undefined && f.portalCount > 0 && f.portalCount < f.totalCount);
    if (filter === "gaps") return sorted.filter(f => f.totalCount !== undefined && f.portalCount < f.totalCount);
    return sorted;
  }

  const TAB = (key: string, label: string) => (
    <button onClick={() => setTab(key as any)} style={{
      background: "none", border: "none",
      color: tab === key ? "#c0c0d8" : "#444",
      fontSize: 11, cursor: "pointer", padding: "6px 0",
      borderBottom: tab === key ? "1px solid #6a8aba" : "1px solid transparent",
      letterSpacing: "0.06em", textTransform: "uppercase" as const,
    }}>{label}</button>
  );

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.72)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#0f1117", border: "1px solid #1e2030", borderRadius: 10,
        width: "100%", maxWidth: 760, maxHeight: "85vh",
        overflowY: "auto", position: "relative",
      }}>
        <button onClick={onClose} title="Close" style={{
          position: "sticky", top: 0, float: "right", width: 28, height: 28,
          margin: "12px 14px 0 0", display: "flex", alignItems: "center",
          justifyContent: "center", background: "transparent", border: "none",
          color: "#444", fontSize: 18, cursor: "pointer", borderRadius: 4, zIndex: 1,
        }}
          onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
          onMouseLeave={e => (e.currentTarget.style.color = "#444")}
        >×</button>

        <div style={{ display: "flex", gap: 20, padding: "28px 32px 0" }}>
          {TAB("coverage", "Coverage")}
          {TAB("growth", "Growth")}
        </div>

        {tab === "coverage" && (
          <div style={{ padding: "28px 32px 32px" }}>
            <div style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
              <div>
                <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
                  Systema Naturae
                </div>
                <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 4 }}>
                  Coverage
                </div>
                <div style={{ fontSize: 13, color: "#555" }}>
                  {totalFamilies} families across {classes.length} classes
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button onClick={toggleAll} style={{
                  background: "none", border: "1px solid #2a2d45", color: "#666",
                  borderRadius: 4, fontSize: 10, padding: "3px 8px", cursor: "pointer",
                }}>
                  {allCollapsed ? "Expand all" : "Collapse all"}
                </button>
                <select value={sort} onChange={e => setSort(e.target.value as SortMode)} style={{
                  background: "#1a1c28", color: "#888", border: "1px solid #2a2d45",
                  borderRadius: 4, fontSize: 10, padding: "3px 6px", cursor: "pointer",
                }}>
                  <option value="gaps">Gaps first</option>
                  <option value="az">A–Z</option>
                </select>
                <select value={filter} onChange={e => setFilter(e.target.value as FilterMode)} style={{
                  background: "#1a1c28", color: "#888", border: "1px solid #2a2d45",
                  borderRadius: 4, fontSize: 10, padding: "3px 6px", cursor: "pointer",
                }}>
                  <option value="all">All</option>
                  <option value="complete">✓ Complete</option>
                  <option value="partial">Partial</option>
                  <option value="gaps">Gaps only</option>
                </select>
              </div>
            </div>

            <div style={{ borderTop: "1px solid #1e2030", marginBottom: 24 }} />

            <div style={{ display: "flex", gap: 16, marginBottom: 16, fontSize: 10 }}>
              {[
                { key: "all", color: "#a0a8b8", label: "All" },
                { key: "complete", color: "#44aa66", label: "✓ Complete" },
                { key: "partial", color: "#cc9944", label: "Partial" },
                { key: "gaps", color: "#444", label: "· Not started" },
              ].map(f => (
                <div key={f.key} onClick={() => setFilter(f.key as FilterMode)} style={{
                  display: "flex", alignItems: "center", gap: 5, cursor: "pointer",
                  opacity: filter === f.key ? 1 : 0.4,
                }}>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: f.color, display: "inline-block" }} />
                  <span style={{ color: "#777" }}>{f.label}</span>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
              {classes.map(cls => {
                const fams = sortedFamilies(cls.families);
                if (fams.length === 0) return null;
                const isOpen = !collapsed.has(cls.id);
                const classPortal = cls.families.reduce((s, f) => s + f.portalCount, 0);
                const classTotal = cls.families.reduce((s, f) => s + (f.totalCount ?? 0), 0);
                const hasAllTotals = cls.families.some(f => f.totalCount !== undefined);
                const classPct = classTotal > 0 ? classPortal / classTotal : 0;
                const traffic = classTraffic(cls.families);
                const isTargetClass = cls.id === initialClassId ||
                  (!initialClassId && initialFamilySlug && cls.families.some(f => f.appSlug === initialFamilySlug));

                return (
                  <div key={cls.id} ref={isTargetClass ? targetRef : undefined}>
                    {/* Class header — clickable to toggle */}
                    <div onClick={() => toggleClass(cls.id)}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        cursor: "pointer", marginBottom: isOpen ? 8 : 0,
                      }}
                    >
                      {/* Chevron */}
                      <span style={{ width: 12, flexShrink: 0, color: "#555", fontSize: 10, textAlign: "center" }}>
                        {isOpen ? "▼" : "▶"}
                      </span>
                      {/* Traffic sign */}
                      <span style={{
                        width: 8, height: 8, borderRadius: "50%",
                        background: TRAFFIC_COLORS[traffic], flexShrink: 0,
                      }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: "#c0c0d8", letterSpacing: "0.03em" }}>
                          {cls.commonName ?? cls.name}
                        </span>
                        {cls.commonName && (
                          <span style={{ fontSize: 11, color: "#444", marginLeft: 8, fontStyle: "italic" }}>{cls.name}</span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: "#444", flexShrink: 0 }}>
                        {fams.length} · {classPortal.toLocaleString()}{hasAllTotals && classTotal > 0 ? ` / ${classTotal.toLocaleString()}` : ""}
                      </div>
                    </div>

                    {/* Mini progress bar */}
                    {isOpen && hasAllTotals && classTotal > 0 && (
                      <div style={{ marginTop: 2, marginBottom: 8, marginLeft: 20, height: 3, background: "#181824", borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${Math.min(100, classPct * 100)}%`, height: "100%", background: classPct >= 1 ? "#44aa66" : "#cc9944", borderRadius: 2 }} />
                      </div>
                    )}

                    {/* Families (only when expanded) */}
                    {isOpen && fams.map(fam => (
                      <CoverageRow key={fam.id} node={fam} depth={0}
                        onFocusFamily={onFocusFamily} onClose={onClose}
                        initiallyOpen={fam.appSlug === initialFamilySlug} />
                    ))}
                  </div>
                );
              })}
            </div>

            {/* Monster families note */}
            <div style={{ borderTop: "1px solid #1e2030", margin: "28px 0 16px" }} />

            <div style={{ fontSize: 10, color: "#444", lineHeight: 1.6, fontStyle: "italic" }}>
              Families with speciesCounts of 150-400+ (Tyrannidae, Thraupidae, Trochilidae, Furnariidae, Columbidae, Muscicapidae, Thamnophilidae, Psittaculidae, Meliphagidae, Pycnonotidae) are shown with their remaining gaps. Full manual curation of such large families is not practical — major genera are represented.
            </div>
          </div>
        )}

        {tab === "growth" && (
          <div style={{ padding: "20px 32px 32px" }}>
            <ImportTimeline />

            {/* Import log list */}
            <LogList />
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- CoverageRow ---------- */

interface RowProps {
  node: CoverageNode;
  depth: number;
  onFocusFamily: (slug: string) => void;
  onClose: () => void;
  initiallyOpen: boolean;
}

function CoverageRow({ node, depth, onFocusFamily, onClose, initiallyOpen }: RowProps) {
  const [open, setOpen] = useState(initiallyOpen);
  const hasChildren = !!node.children && node.children.length > 0;
  const hasCoverage = node.totalCount !== undefined;
  const tag = statusText(node.portalCount, node.totalCount);
  const tcol = tagColor(node.portalCount, node.totalCount);
  const isClickable = !!node.appSlug && depth === 0;

  return (
    <div>
      <div
        onClick={() => {
          if (hasChildren && !hasCoverage) setOpen(!open);
          else if (hasChildren) setOpen(!open);
          else if (isClickable) { onFocusFamily(node.appSlug!); onClose(); }
        }}
        style={{
          display: "flex", alignItems: "center", gap: 6,
          padding: "5px 8px", borderRadius: 5,
          cursor: hasChildren || isClickable ? "pointer" : "default",
          marginLeft: depth * 16, background: "transparent",
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = "#1a1c28"; }}
        onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
      >
        <span style={{ width: 14, flexShrink: 0, color: "#555", fontSize: 10, textAlign: "center", visibility: hasChildren ? "visible" : "hidden" }}>
          {open ? "▼" : "▶"}
        </span>

        <span style={{
          fontSize: depth === 0 ? 10 : 9, color: tcol,
          minWidth: depth === 0 ? 36 : 24, textAlign: "right" as const,
          fontFamily: "monospace", flexShrink: 0,
        }}>{tag}</span>

        <div style={{ minWidth: 0, flex: 1 }}>
          <span style={{
            fontSize: depth === 0 ? 12 : 11, fontWeight: depth <= 1 ? 500 : 400,
            color: depth === 0 ? "#c8c8d8" : "#a0a8b8",
            whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", display: "block",
          }}>
            {node.commonName && ["FAMILY", "SUBFAMILY"].includes(node.rank) ? node.commonName : node.name}
          </span>
          {node.commonName && ["FAMILY", "SUBFAMILY"].includes(node.rank) && (
            <span style={{ fontSize: 10, color: "#555", display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {node.name}
            </span>
          )}
        </div>

        <div style={{ flexShrink: 0, fontSize: depth === 0 ? 11 : 10, color: "#666", textAlign: "right" }}>
          {node.portalCount.toLocaleString()}
          {hasCoverage ? ` / ${node.totalCount!.toLocaleString()}` : depth === 0 ? " in portal" : ""}
        </div>
      </div>

      {open && hasChildren && (
        <div>
          {node.children!.map(c => (
            <CoverageRow key={c.id} node={c} depth={depth + 1} onFocusFamily={onFocusFamily} onClose={onClose} initiallyOpen={false} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- LogList ---------- */

interface ImportEvent {
  date: string;
  speciesAdded: number;
  speciesRunning: number;
  families: string[];
}

function LogList() {
  const data = (importLog as ImportEvent[]).filter(d => d.speciesRunning > 0).reverse();

  return (
    <div style={{ marginTop: 16, borderTop: "1px solid #1e2030", paddingTop: 14 }}>
      <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
        Import log
      </div>
      <div style={{ maxHeight: 180, overflowY: "auto", fontSize: 10, lineHeight: 1.7 }}>
        {data.map((d, i) => {
          const date = new Date(d.date).toLocaleDateString("en-GB", { month: "short", day: "numeric" });
          const famList = d.families.length > 5
            ? d.families.slice(0, 5).join(", ") + ` +${d.families.length - 5}`
            : d.families.join(", ");
          return (
            <div key={i} style={{ display: "flex", gap: 8, padding: "2px 4px", borderRadius: 3, color: "#666" }}
              onMouseEnter={e => (e.currentTarget.style.background = "#1a1c28")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
            >
              <span style={{ color: "#888", flexShrink: 0, width: 56 }}>{date}</span>
              <span style={{ color: "#8aba6a", flexShrink: 0, width: 50, textAlign: "right" as const }}>+{d.speciesAdded}</span>
              <span style={{ color: "#6a8aba", flexShrink: 0, width: 50, textAlign: "right" as const }}>{d.speciesRunning}</span>
              <span style={{ color: "#555", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{famList}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
