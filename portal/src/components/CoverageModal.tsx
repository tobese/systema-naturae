import { useEffect, useMemo, useRef, useState } from "react";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "../types";
import ImportTimeline from "./ImportTimeline";

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
    id: node.id,
    name: node.name,
    commonName: node.commonName,
    rank: node.rank,
    appSlug: pn.appSlug,
    portalCount: countSpecies(node),
    totalCount: pn.speciesCount,
  };
  const children = (node.children ?? [])
    .map(buildCoverageTree)
    .filter((c): c is CoverageNode => c !== null);
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
      (node.children ?? []).forEach(c => walk(c, cls));
      return;
    }
    if (node.rank === "FAMILY") {
      const tree = buildCoverageTree(node);
      if (tree) (currentClass ?? other).families.push(tree);
      return;
    }
    (node.children ?? []).forEach(c => walk(c, currentClass));
  }

  walk(root, null);
  if (other.families.length > 0) classes.push(other);
  return classes;
}

function coverageDotColor(portalCount: number, totalCount?: number): string {
  if (portalCount === 0) return "#444";
  if (totalCount !== undefined && portalCount >= totalCount) return "#44aa66";
  return "#cc9944";
}

function CoverageRow({ node, depth, onFocusFamily, onClose, initiallyOpen }: {
  node: CoverageNode;
  depth: number;
  onFocusFamily: (slug: string) => void;
  onClose: () => void;
  initiallyOpen: boolean;
}) {
  const [open, setOpen] = useState(initiallyOpen);
  const hasChildren = !!node.children && node.children.length > 0;
  const hasCoverage = node.totalCount !== undefined;

  const dotColor = coverageDotColor(node.portalCount, node.totalCount);
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
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "5px 8px",
          borderRadius: 5,
          cursor: hasChildren || isClickable ? "pointer" : "default",
          marginLeft: depth * 16,
          background: "transparent",
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = "#1a1c28"; }}
        onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
      >
        {/* Chevron */}
        <span style={{
          width: 14,
          flexShrink: 0,
          color: "#555",
          fontSize: 10,
          textAlign: "center",
          visibility: hasChildren ? "visible" : "hidden",
        }}>
          {open ? "▼" : "▶"}
        </span>

        {/* Dot */}
        <span style={{
          width: depth === 0 ? 7 : 5,
          height: depth === 0 ? 7 : 5,
          borderRadius: "50%",
          background: dotColor,
          flexShrink: 0,
        }} />

        {/* Name */}
        <div style={{ minWidth: 0, flex: 1 }}>
          <span style={{
            fontSize: depth === 0 ? 12 : 11,
            fontWeight: depth <= 1 ? 500 : 400,
            color: depth === 0 ? "#c8c8d8" : "#a0a8b8",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "block",
          }}>
            {node.commonName && ["FAMILY", "SUBFAMILY"].includes(node.rank) ? node.commonName : node.name}
          </span>
          {node.commonName && ["FAMILY", "SUBFAMILY"].includes(node.rank) && (
            <span style={{ fontSize: 10, color: "#555", display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {node.name}
            </span>
          )}
        </div>

        {/* Count */}
        <div style={{ flexShrink: 0, fontSize: depth === 0 ? 11 : 10, color: "#666", textAlign: "right" }}>
          {node.portalCount.toLocaleString()}
          {hasCoverage ? ` / ${node.totalCount!.toLocaleString()}` : depth === 0 ? " in portal" : ""}
        </div>
      </div>

      {/* Children */}
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

export default function CoverageModal({ data, onClose, onFocusFamily, initialFamilySlug, initialClassId }: Props) {
  const [tab, setTab] = useState<"coverage" | "growth">("coverage");
  const targetRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const classes = useMemo(() => buildCoverage(data), [data]);
  const totalFamilies = useMemo(() => classes.reduce((sum, cls) => sum + cls.families.length, 0), [classes]);

  const TAB = (key: string, label: string) => (
    <button
      onClick={() => setTab(key as any)}
      style={{
        background: "none",
        border: "none",
        color: tab === key ? "#c0c0d8" : "#444",
        fontSize: 11,
        cursor: "pointer",
        padding: "6px 0",
        borderBottom: tab === key ? "1px solid #6a8aba" : "1px solid transparent",
        letterSpacing: "0.06em",
        textTransform: "uppercase" as const,
      }}
    >
      {label}
    </button>
  );

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.72)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "#0f1117",
          border: "1px solid #1e2030",
          borderRadius: 10,
          width: "100%",
          maxWidth: tab === "growth" ? 740 : 760,
          maxHeight: "85vh",
          overflowY: "auto",
          position: "relative",
        }}
      >
        <button
          onClick={onClose}
          title="Close"
          style={{
            position: "sticky",
            top: 0,
            float: "right",
            width: 28,
            height: 28,
            margin: "12px 14px 0 0",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "transparent",
            border: "none",
            color: "#444",
            fontSize: 18,
            cursor: "pointer",
            borderRadius: 4,
            zIndex: 1,
          }}
          onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
          onMouseLeave={e => (e.currentTarget.style.color = "#444")}
        >
          ×
        </button>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 20, padding: "28px 32px 0" }}>
          {TAB("coverage", "Coverage")}
          {TAB("growth", "Growth")}
        </div>

        {tab === "coverage" && (
        <div style={{ padding: "28px 32px 32px" }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
              Systema Naturae
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 6 }}>
              Coverage
            </div>
            <div style={{ fontSize: 13, color: "#555" }}>
              {totalFamilies} families across {classes.length} classes
            </div>
          </div>

          <div style={{ borderTop: "1px solid #1e2030", marginBottom: 24 }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
            {classes.map(cls => {
              const classPortal = cls.families.reduce((s, f) => s + f.portalCount, 0);
              const classTotal = cls.families.reduce((s, f) => {
                if (f.totalCount === undefined) return s;
                return s + f.totalCount;
              }, 0);
              const hasAllTotals = cls.families.every(f => f.totalCount !== undefined);
              const isTargetClass = cls.id === initialClassId ||
                (!initialClassId && initialFamilySlug && cls.families.some(f => f.appSlug === initialFamilySlug));

              return (
                <div key={cls.id} ref={isTargetClass ? targetRef : undefined}>
                  <div style={{
                    display: "flex",
                    alignItems: "baseline",
                    justifyContent: "space-between",
                    marginBottom: 6,
                    paddingBottom: 6,
                    borderBottom: "1px solid #181824",
                  }}>
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#c0c0d8", letterSpacing: "0.03em" }}>
                        {cls.commonName ?? cls.name}
                      </span>
                      {cls.commonName && (
                        <span style={{ fontSize: 11, color: "#444", marginLeft: 8, fontStyle: "italic" }}>
                          {cls.name}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: "#444" }}>
                      {cls.families.length} {cls.families.length === 1 ? "family" : "families"}
                      {" · "}
                      {classPortal.toLocaleString()}
                      {hasAllTotals && classTotal > 0 ? ` of ${classTotal.toLocaleString()}` : ""}
                      {" in portal"}
                    </div>
                  </div>

                  {cls.families.map(fam => (
                    <CoverageRow
                      key={fam.id}
                      node={fam}
                      depth={0}
                      onFocusFamily={onFocusFamily}
                      onClose={onClose}
                      initiallyOpen={fam.appSlug === initialFamilySlug}
                    />
                  ))}
                </div>
              );
            })}
          </div>

          <div style={{ borderTop: "1px solid #1e2030", margin: "28px 0 20px" }} />

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div style={{ display: "flex", gap: 20 }}>
              {[
                { dot: "#44aa66", label: "All known species in portal" },
                { dot: "#cc9944", label: "Partially covered" },
                { dot: "#444", label: "Not yet imported" },
              ].map(({ dot, label }) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: dot, display: "inline-block" }} />
                  <span style={{ fontSize: 11, color: "#555" }}>{label}</span>
                </div>
              ))}
            </div>
            <span style={{ fontSize: 11, color: "#333", fontStyle: "italic" }}>
              counts: species in portal / known to science
            </span>
          </div>
        </div>
        )}

        {tab === "growth" && (
          <div style={{ padding: "20px 32px 32px" }}>
            <ImportTimeline />
          </div>
        )}
      </div>
    </div>
  );
}
