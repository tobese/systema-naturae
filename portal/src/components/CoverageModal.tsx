import { useEffect, useMemo, useRef } from "react";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "../types";

interface Props {
  data: TaxonNode;
  onClose: () => void;
  onFocusFamily: (slug: string) => void;
  initialFamilySlug?: string | null;
  initialClassId?: string | null;
}

interface FamilyCoverage {
  id: string;
  name: string;
  commonName?: string;
  appSlug?: string;
  portalCount: number;
  totalCount?: number;
}

interface ClassCoverage {
  id: string;
  name: string;
  commonName?: string;
  families: FamilyCoverage[];
}

function countSpecies(node: TaxonNode): number {
  if (node.rank === "SPECIES") return 1;
  return (node.children ?? []).reduce((sum, c) => sum + countSpecies(c), 0);
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
      const pn = node as PortalNode;
      const fam: FamilyCoverage = {
        id: node.id,
        name: node.name,
        commonName: node.commonName,
        appSlug: pn.appSlug,
        portalCount: countSpecies(node),
        totalCount: pn.speciesCount,
      };
      (currentClass ?? other).families.push(fam);
      return;
    }
    (node.children ?? []).forEach(c => walk(c, currentClass));
  }

  walk(root, null);
  if (other.families.length > 0) classes.push(other);
  return classes;
}

function coverageColor(portalCount: number, totalCount?: number): string {
  if (portalCount === 0) return "#333";
  if (totalCount !== undefined && portalCount >= totalCount) return "#336644";
  return "#7a5520";
}

function coverageDotColor(portalCount: number, totalCount?: number): string {
  if (portalCount === 0) return "#444";
  if (totalCount !== undefined && portalCount >= totalCount) return "#44aa66";
  return "#cc9944";
}

export default function CoverageModal({ data, onClose, onFocusFamily, initialFamilySlug, initialClassId }: Props) {
  const targetRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    if (targetRef.current) {
      targetRef.current.scrollIntoView({ behavior: "instant", block: "center" });
    }
  }, []);

  const classes = useMemo(() => buildCoverage(data), [data]);

  const totalFamilies = useMemo(() => classes.reduce((sum, cls) => sum + cls.families.length, 0), [classes]);

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
          maxWidth: 760,
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
                    marginBottom: 10,
                    paddingBottom: 8,
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

                  <div style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 4,
                  }}>
                    {cls.families.map(fam => {
                      const dotColor = coverageDotColor(fam.portalCount, fam.totalCount);
                      const bgColor = coverageColor(fam.portalCount, fam.totalCount);
                      const isClickable = !!fam.appSlug;
                      const isSelected = !!initialFamilySlug && fam.appSlug === initialFamilySlug;
                      return (
                        <div
                          key={fam.id}
                          ref={isSelected ? targetRef : undefined}
                          onClick={isClickable ? () => { onFocusFamily(fam.appSlug!); onClose(); } : undefined}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: 8,
                            padding: "6px 10px",
                            borderRadius: 6,
                            border: isSelected ? "1px solid #5a7aaa" : `1px solid ${bgColor}`,
                            background: isSelected ? "#1a2a3a" : `${bgColor}22`,
                            cursor: isClickable ? "pointer" : "default",
                            width: "calc(50% - 2px)",
                            boxSizing: "border-box",
                            minWidth: 0,
                          }}
                          onMouseEnter={e => {
                            if (isClickable) {
                              (e.currentTarget as HTMLDivElement).style.background = `${bgColor}44`;
                            }
                          }}
                          onMouseLeave={e => {
                            (e.currentTarget as HTMLDivElement).style.background = `${bgColor}22`;
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                            <span style={{
                              width: 7,
                              height: 7,
                              borderRadius: "50%",
                              background: dotColor,
                              flexShrink: 0,
                            }} />
                            <div style={{ minWidth: 0 }}>
                              <span style={{ fontSize: 12, fontWeight: 500, color: "#c8c8d8", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", display: "block" }}>
                                {fam.name}
                              </span>
                              {fam.commonName && (
                                <span style={{ fontSize: 10, color: "#555", display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                  {fam.commonName}
                                </span>
                              )}
                            </div>
                          </div>
                          <div style={{ flexShrink: 0, fontSize: 11, color: "#555", textAlign: "right" }}>
                            {fam.portalCount.toLocaleString()}
                            {fam.totalCount !== undefined ? ` of ${fam.totalCount.toLocaleString()}` : ""}
                          </div>
                        </div>
                      );
                    })}
                  </div>
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
      </div>
    </div>
  );
}
