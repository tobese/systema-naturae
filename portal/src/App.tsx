import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import FamilyTree from "@shared/components/FamilyTree";
import HabitatMap from "@shared/components/HabitatMap";
import NodeNav from "@shared/components/NodeNav";
import type { TaxonNode } from "@shared/types";
import type { PortalNode } from "./types";
import { annotatePortalLevels } from "./colors";
import { useUnifiedTree } from "./hooks/useUnifiedTree";
import { useUrlState } from "./hooks/useUrlState";
import UnifiedInfoPanel from "./components/UnifiedInfoPanel";
import SearchBox from "./components/SearchBox";
import NewsBell from "./components/NewsBell";
import InfoModal from "./components/InfoModal";
import CoverageModal from "./components/CoverageModal";
import EponymModal from "./components/EponymModal";
import InternationalDaysModal from "./components/InternationalDaysModal";
import TaxonomySidebar from "./components/TaxonomySidebar";
import { useInternationalDays } from "./hooks/useInternationalDays";
import SpeciesOfTheDayModal from "./components/SpeciesOfTheDayModal";
import { useSpeciesOfTheDay } from "./hooks/useSpeciesOfTheDay";
import rawJson from "../data/unified-taxonomy.json";

const annotatedData = annotatePortalLevels(rawJson as TaxonNode);

function walkFind(node: TaxonNode, id: string): TaxonNode | null {
  if (node.id === id) return node;
  for (const child of node.children ?? []) {
    const found = walkFind(child, id);
    if (found) return found;
  }
  return null;
}

function getPathToNode(root: TaxonNode, targetId: string): TaxonNode[] {
  function walk(node: TaxonNode, path: TaxonNode[]): TaxonNode[] | null {
    const next = [...path, node];
    if (node.id === targetId) return next;
    for (const child of node.children ?? []) {
      const found = walk(child, next);
      if (found) return found;
    }
    return null;
  }
  return walk(root, []) ?? [];
}

function findNavContext(
  tree: TaxonNode,
  targetId: string,
): { parent: TaxonNode | null; siblings: TaxonNode[]; index: number } {
  if (tree.id === targetId) return { parent: null, siblings: [], index: 0 };
  function walk(node: TaxonNode): { parent: TaxonNode; siblings: TaxonNode[]; index: number } | null {
    const children = node.children ?? [];
    const idx = children.findIndex(c => c.id === targetId);
    if (idx !== -1) return { parent: node, siblings: children, index: idx };
    for (const child of children) {
      const found = walk(child);
      if (found) return found;
    }
    return null;
  }
  return walk(tree) ?? { parent: null, siblings: [], index: 0 };
}

export default function App() {
  const [layout, setLayout] = useState<"radial" | "vertical">("radial");
  const [showInfo, setShowInfo] = useState(false);
  const [showCoverage, setShowCoverage] = useState(false);
  const [showEponyms, setShowEponyms] = useState(false);
  const [showDays, setShowDays] = useState(false);
  const [showSotd, setShowSotd] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [now, setNow] = useState(new Date());
  const { todaysDays } = useInternationalDays();
  const speciesOfTheDay = useSpeciesOfTheDay(annotatedData);
  const [expandedSubspeciesIds, setExpandedSubspeciesIds] = useState<Set<string>>(new Set());
  const [expandedBreedIds, setExpandedBreedIds] = useState<Set<string>>(new Set());
  const [highlightedContinent, setHighlightedContinent] = useState<string | null>(null);
  const pendingZoomId = useRef<string | null>(null);
  const sidebarScrollRef = useRef<HTMLDivElement>(null);

  const { focusedFamilySlug, focusedClassId, selectedNodeId, setFocus, setFocusedClass, setSelectedNodeId, navigateTo } = useUrlState();

  useEffect(() => {
    sidebarScrollRef.current?.scrollTo({ top: 0, behavior: "instant" });
  }, [selectedNodeId]);

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(id);
  }, []);

  // selected node is fully URL-driven so browser back/forward and deep-links work correctly
  const selected = useMemo(
    () => (selectedNodeId ? walkFind(annotatedData, selectedNodeId) : null),
    [selectedNodeId],
  );

  // Resolve focused family slug → node id
  const focusedFamilyId = useMemo(() => {
    if (!focusedFamilySlug) return null;
    function find(n: TaxonNode): string | null {
      if (n.rank === "FAMILY" && n.familySlug === focusedFamilySlug) return n.id;
      for (const c of n.children ?? []) { const r = find(c); if (r) return r; }
      return null;
    }
    return find(annotatedData);
  }, [focusedFamilySlug]);

  const { treeData, colorTheme, highlightedNodeIds, findNodeById } = useUnifiedTree(
    annotatedData,
    focusedFamilyId,
    expandedSubspeciesIds,
    expandedBreedIds,
    highlightedContinent,
  );

  const handleSelect = useCallback((node: TaxonNode | null) => {
    if (!node) { setSelectedNodeId(null); return; }

    // KINGDOM/PHYLUM click → clear class focus, select this node (single atomic update)
    if (node.rank === "KINGDOM" || node.rank === "PHYLUM") {
      setFocusedClass(null, node.id);
      return;
    }

    // CLASS node click → focus / unfocus (compresses other classes to 35% of arc)
    if (node.rank === "CLASS") {
      if (node.id === focusedClassId) {
        setFocusedClass(null, null);
      } else {
        setFocusedClass(node.id, node.id);
        pendingZoomId.current = node.id;
      }
      return;
    }

    // FAMILY node click → focus / unfocus
    if (node.rank === "FAMILY") {
      const slug = node.familySlug ?? null;
      if (slug === focusedFamilySlug) {
        setFocus(null);
        setExpandedSubspeciesIds(new Set());
        setExpandedBreedIds(new Set());
        setHighlightedContinent(null);
      } else {
        navigateTo(slug, node.id);
        setExpandedSubspeciesIds(new Set());
        setExpandedBreedIds(new Set());
        setHighlightedContinent(null);
        pendingZoomId.current = node.id;
      }
      return;
    }

    // Node is outside the currently focused family → navigate to its context
    if (focusedFamilySlug && node.familySlug !== focusedFamilySlug) {
      setExpandedSubspeciesIds(new Set());
      setExpandedBreedIds(new Set());
      setHighlightedContinent(null);
      navigateTo(node.familySlug ?? null, node.id);
      if (node.familySlug) pendingZoomId.current = node.id;
      return;
    }

    // SPECIES with subspecies/breeds → toggle expansion
    if (node.rank === "SPECIES") {
      const fullNode = walkFind(annotatedData, node.id);
      const hasSubspecies = fullNode?.children?.some(c => c.rank === "SUBSPECIES") ?? false;
      const hasBreeds = fullNode?.children?.some(c => c.rank === "BREED_GROUP") ?? false;

      if (hasSubspecies) {
        setExpandedSubspeciesIds(prev => {
          const next = new Set(prev);
          if (next.has(node.id)) next.delete(node.id);
          else { next.add(node.id); pendingZoomId.current = node.id; }
          return next;
        });
      } else if (hasBreeds) {
        setExpandedBreedIds(prev => {
          const next = new Set(prev);
          if (next.has(node.id)) next.delete(node.id);
          else { next.add(node.id); pendingZoomId.current = node.id; }
          return next;
        });
      }
    }

    // Zoom to order-and-below so the tree pans to the destination (skip CLASS/PHYLUM — too jarring in overview)
    const ZOOM_RANKS = new Set(["ORDER", "SUBFAMILY", "TRIBE", "GENUS", "BREED_GROUP", "HYBRID_GROUP"]);
    if (ZOOM_RANKS.has(node.rank)) {
      pendingZoomId.current = node.id;
    }

    // Toggle selection: clicking same node deselects
    setSelectedNodeId(selectedNodeId === node.id ? null : node.id);
  }, [focusedFamilySlug, selectedNodeId, setFocus, setSelectedNodeId, navigateTo]);

  const handleCollapseFamily = useCallback(() => {
    if (focusedFamilyId) pendingZoomId.current = focusedFamilyId;
    setFocus(null);
    setExpandedSubspeciesIds(new Set());
    setExpandedBreedIds(new Set());
    setHighlightedContinent(null);
  }, [setFocus, focusedFamilyId]);

  const handleCollapseClass = useCallback(() => {
    setFocusedClass(null, null);
  }, [setFocusedClass]);

  const selectedInTree = useMemo(
    () => selected ? (walkFind(treeData, selected.id) ?? selected) : null,
    [selected, treeData],
  );

  const navContext = useMemo(
    () => selected ? findNavContext(treeData, selected.id) : null,
    [selected, treeData],
  );

  const focusedFamilyNode = useMemo(
    () => focusedFamilyId ? walkFind(annotatedData, focusedFamilyId) : null,
    [focusedFamilyId],
  );

  const focusedClassNode = useMemo(
    () => focusedClassId ? walkFind(annotatedData, focusedClassId) : null,
    [focusedClassId],
  );

  const breadcrumbPath = useMemo(
    () => selected ? getPathToNode(treeData, selected.id) : [],
    [selected, treeData],
  );

  const subfamiliesForPanel = useMemo(() => {
    if (!focusedFamilyId || !focusedFamilyNode) return [];
    return (focusedFamilyNode.children ?? []).filter(
      c => c.rank === "SUBFAMILY" || c.rank === "TRIBE",
    );
  }, [focusedFamilyId, focusedFamilyNode]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "A") return;
      if (e.key === "Escape" && focusedFamilySlug) { handleCollapseFamily(); return; }
      if (e.key === "Escape" && focusedClassId) { handleCollapseClass(); return; }
      if (!selected || !navContext) return;
      const { parent, siblings, index } = navContext;
      if (e.key === "ArrowLeft") {
        if (siblings.length > 1) handleSelect(siblings[(index - 1 + siblings.length) % siblings.length]);
      } else if (e.key === "ArrowRight") {
        if (siblings.length > 1) handleSelect(siblings[(index + 1) % siblings.length]);
      } else if (e.key === "ArrowUp" && parent) {
        e.preventDefault();
        handleSelect(parent);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, navContext, handleSelect, focusedFamilySlug, handleCollapseFamily, focusedClassId, handleCollapseClass]);

  const totalSpecies = useMemo(() => {
    let n = 0;
    function walk(node: TaxonNode) {
      if (node.rank === "FAMILY") { n += (node as PortalNode).speciesCount ?? 0; return; }
      node.children?.forEach(walk);
    }
    walk(annotatedData);
    return n;
  }, []);

  const totalNodes = useMemo(() => {
    let n = 0;
    function walk(node: TaxonNode) { n++; node.children?.forEach(walk); }
    walk(annotatedData);
    return n;
  }, []);

  const formattedDatetime = now.toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });

  const rankCounts = useMemo(() => {
    const counts = { CLASS: 0, ORDER: 0, FAMILY: 0, LEAVES: 0 };
    const root = focusedClassId && focusedClassNode ? focusedClassNode : annotatedData;
    function walk(node: TaxonNode) {
      if (node.rank === "CLASS") counts.CLASS++;
      else if (node.rank === "PHYLUM" && !node.children?.some(c => c.rank === "CLASS")) counts.CLASS++;
      else if (node.rank === "ORDER") counts.ORDER++;
      else if (node.rank === "FAMILY") counts.FAMILY++;
      if (!node.children || node.children.length === 0) counts.LEAVES++;
      node.children?.forEach(walk);
    }
    walk(root);
    return counts;
  }, [focusedClassId, focusedClassNode]);

  const RANK_TIERS = [
    { rank: "CLASS" as const,  label: "Classes",  singular: "Class",  color: "#7a6a4a", bg: "#1e1a0e" },
    { rank: "ORDER" as const,  label: "Orders",   singular: "Order",  color: "#4a7a6a", bg: "#0e1e1a" },
    { rank: "FAMILY" as const, label: "Families", singular: "Family", color: "#4a6a9a", bg: "#0e1628" },
    { rank: "LEAVES" as const, label: "total",    singular: "total",  color: "#6a6a8a", bg: "#141420" },
  ];

  const btnBase: React.CSSProperties = {
    padding: "6px 14px",
    borderRadius: 6,
    border: "1px solid",
    fontSize: 13,
    cursor: "pointer",
  };

  const inFamilyFocus = focusedFamilySlug !== null;

  const contextSpecies = useMemo(() => {
    if (inFamilyFocus && focusedFamilyNode) {
      let n = 0;
      function walkFamily(node: TaxonNode) {
        if (node.rank === "SPECIES") { n++; return; }
        node.children?.forEach(walkFamily);
      }
      walkFamily(focusedFamilyNode);
      return n;
    }
    if (focusedClassId && focusedClassNode) {
      let n = 0;
      function walk(node: TaxonNode) {
        if (node.rank === "FAMILY") { n += (node as PortalNode).speciesCount ?? 0; return; }
        node.children?.forEach(walk);
      }
      walk(focusedClassNode);
      return n;
    }
    return totalSpecies;
  }, [inFamilyFocus, focusedFamilyNode, focusedClassId, focusedClassNode, totalSpecies]);
  const hasContinentData = selected?.rank === "SPECIES" || selected?.rank === "SUBSPECIES";

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "#0f1117",
      color: "#e0e0e0",
      fontFamily: "'SF Pro Text', 'Helvetica Neue', system-ui, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        borderBottom: "1px solid #1e2030",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>Systema Naturae</span>
            {(inFamilyFocus || focusedClassId) && (
              <span style={{ fontSize: 13, color: "#555" }}>
                {inFamilyFocus
                  ? `${focusedFamilyNode?.commonName ?? focusedFamilyNode?.name ?? ""} · ${contextSpecies.toLocaleString()} species`
                  : (focusedClassNode?.commonName ?? focusedClassNode?.name ?? "")}
              </span>
            )}
          </div>
          {!inFamilyFocus && (
            <div style={{ display: "flex", alignItems: "center", marginTop: 5 }}>
              {RANK_TIERS.map(({ rank, label, singular, color, bg }, i) => (
                <div key={rank} style={{
                  clipPath: i === 0
                    ? "polygon(0 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 0 100%)"
                    : i === RANK_TIERS.length - 1
                      ? "polygon(10px 0, 100% 0, 100% 100%, 10px 100%, 0 50%)"
                      : "polygon(10px 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 10px 100%, 0 50%)",
                  background: bg,
                  marginLeft: i === 0 ? 0 : -1,
                  padding: `3px 14px 3px ${i === 0 ? "10px" : "18px"}`,
                  fontSize: 11,
                  color,
                  letterSpacing: "0.02em",
                  whiteSpace: "nowrap",
                }}>
                  {rankCounts[rank].toLocaleString()} {rankCounts[rank] === 1 ? singular : label}
                </div>
              ))}
            </div>
          )}
          {speciesOfTheDay && (
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ fontSize: 11, color: "#556" }}>✦</span>
              <button
                onClick={() => setShowSotd(true)}
                style={{ background: "none", border: "none", padding: 0, cursor: "pointer", fontSize: 12, color: "#4a5070", letterSpacing: "0.01em" }}
                onMouseEnter={e => { e.currentTarget.style.color = "#7080a0"; }}
                onMouseLeave={e => { e.currentTarget.style.color = "#4a5070"; }}
              >
                {speciesOfTheDay.commonName ?? speciesOfTheDay.name}
              </button>
              <span style={{ fontSize: 12, color: "#222" }}>—</span>
              <span style={{ fontSize: 12, color: "#333", fontStyle: "italic" }}>{speciesOfTheDay.name}</span>
            </div>
          )}
          {todaysDays.length > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ fontSize: 11, color: "#5a9a5a" }}>🌿</span>
              <button
                onClick={() => setShowDays(true)}
                style={{ background: "none", border: "none", padding: 0, cursor: "pointer", fontSize: 12, color: "#4a7a4a", letterSpacing: "0.01em" }}
                onMouseEnter={e => { e.currentTarget.style.color = "#6a9a6a"; }}
                onMouseLeave={e => { e.currentTarget.style.color = "#4a7a4a"; }}
              >
                {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric" })}
              </button>
              <span style={{ fontSize: 12, color: "#333" }}>·</span>
              {todaysDays.map((d, i) => (
                <span key={d.id} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  {i > 0 && <span style={{ fontSize: 12, color: "#333" }}>·</span>}
                  <button
                    onClick={() => d.relatedFamilies?.[0] ? setFocus(d.relatedFamilies[0].slug) : setShowDays(true)}
                    style={{ background: "none", border: "none", padding: 0, cursor: "pointer", fontSize: 12, color: "#6aaa6a", letterSpacing: "0.01em" }}
                    onMouseEnter={e => { e.currentTarget.style.color = "#8acc8a"; }}
                    onMouseLeave={e => { e.currentTarget.style.color = "#6aaa6a"; }}
                  >
                    {d.title}
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => setShowSidebar(o => !o)}
          title="Taxonomy sidebar"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 34,
            height: 34,
            padding: 0,
            borderRadius: 6,
            border: "1px solid",
            borderColor: showSidebar ? "#3a3d50" : "#1e2030",
            background: showSidebar ? "#1e2030" : "transparent",
            color: showSidebar ? "#c0c0d8" : "#444",
            cursor: "pointer",
            fontSize: 16,
            marginRight: 6,
          }}
          onMouseEnter={e => { if (!showSidebar) e.currentTarget.style.color = "#888"; }}
          onMouseLeave={e => { if (!showSidebar) e.currentTarget.style.color = "#444"; }}
        >
          ☰
        </button>
        <SearchBox data={annotatedData} onNavigate={navigateTo} />
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <button
            onClick={() => setShowInfo(o => !o)}
            title="About Systema Naturae"
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 34,
              height: 34,
              padding: 0,
              borderRadius: 6,
              border: "1px solid",
              borderColor: showInfo ? "#3a3d50" : "#1e2030",
              background: showInfo ? "#1e2030" : "transparent",
              color: showInfo ? "#c0c0d8" : "#444",
              cursor: "pointer",
              fontSize: 15,
            }}
            onMouseEnter={e => { if (!showInfo) e.currentTarget.style.color = "#888"; }}
            onMouseLeave={e => { if (!showInfo) e.currentTarget.style.color = "#444"; }}
          >
            ⓘ
          </button>
          <button
            onClick={() => setShowEponyms(o => !o)}
            title="Species named after people"
            style={{
              ...btnBase,
              borderColor: showEponyms ? "#3a3d50" : "#1e2030",
              background: showEponyms ? "#1e2030" : "transparent",
              color: showEponyms ? "#c0c0d8" : "#555",
            }}
            onMouseEnter={e => { if (!showEponyms) e.currentTarget.style.color = "#888"; }}
            onMouseLeave={e => { if (!showEponyms) e.currentTarget.style.color = "#555"; }}
          >
            Eponyms
          </button>
          <button
            onClick={() => setShowCoverage(o => !o)}
            title="Taxonomy coverage"
            style={{
              ...btnBase,
              borderColor: showCoverage ? "#3a3d50" : "#1e2030",
              background: showCoverage ? "#1e2030" : "transparent",
              color: showCoverage ? "#c0c0d8" : "#555",
            }}
            onMouseEnter={e => { if (!showCoverage) e.currentTarget.style.color = "#888"; }}
            onMouseLeave={e => { if (!showCoverage) e.currentTarget.style.color = "#555"; }}
          >
            Coverage
          </button>
          <NewsBell />
          <button
            onClick={() => setShowDays(o => !o)}
            title="International Nature Days"
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 34,
              height: 34,
              padding: 0,
              borderRadius: 6,
              border: "1px solid",
              borderColor: showDays ? "#3a3d50" : "#1e2030",
              background: showDays ? "#1e2030" : "transparent",
              color: showDays ? "#c0c0d8" : "#444",
              cursor: "pointer",
            }}
            onMouseEnter={e => { if (!showDays) e.currentTarget.style.color = "#888"; }}
            onMouseLeave={e => { if (!showDays) e.currentTarget.style.color = "#444"; }}
          >
            <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z" />
              <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
            </svg>
            {todaysDays.length > 0 && (
              <span style={{
                position: "absolute",
                top: 5,
                right: 5,
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#80b880",
                border: "1.5px solid #0f1117",
              }} />
            )}
          </button>
          {inFamilyFocus && (
            <button
              onClick={handleCollapseFamily}
              style={{ ...btnBase, borderColor: "#303048", background: "#141420", color: "#8899cc", marginRight: 4 }}
            >
              ← All families
            </button>
          )}
          {!inFamilyFocus && focusedClassId && (
            <button
              onClick={handleCollapseClass}
              style={{ ...btnBase, borderColor: "#303048", background: "#141420", color: "#8899cc", marginRight: 4 }}
            >
              ← All classes
            </button>
          )}
          {(["radial", "vertical"] as const).map(l => (
            <button
              key={l}
              onClick={() => setLayout(l)}
              style={{
                ...btnBase,
                borderColor: layout === l ? "#3a3d50" : "#1e2030",
                background: layout === l ? "#1e2030" : "transparent",
                color: layout === l ? "#e0e0e0" : "#555",
              }}
            >
              {l === "radial" ? "⊕ Radial" : "⇒ Vertical"}
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {showSidebar && (
          <div style={{
            width: 220,
            borderRight: "1px solid #1e2030",
            overflow: "hidden",
            flexShrink: 0,
          }}>
            <TaxonomySidebar
              data={annotatedData}
              focusedClassId={focusedClassId}
              focusedFamilySlug={focusedFamilySlug}
              selectedId={selected?.id ?? null}
              onSelect={handleSelect}
              onFocusFamily={setFocus}
              onFocusClass={setFocusedClass}
            />
          </div>
        )}
        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
          <FamilyTree
            data={treeData}
            layout={layout}
            onSelect={handleSelect}
            selectedId={selected?.id ?? null}
            pendingZoomId={pendingZoomId}
            highlightedNodeIds={highlightedNodeIds}
            colorTheme={colorTheme}
            focusedFamilySlug={focusedFamilySlug}
            focusedClassId={focusedClassId}
          />
          <div style={{
            position: "absolute",
            bottom: 16,
            right: 16,
            width: 96,
            height: 110,
            pointerEvents: "none",
          }}>
            <div style={{
              position: "absolute",
              inset: 6,
              borderRadius: "50%",
              background: "rgba(10,10,20,0.55)",
            }} />
            <img
              src={`${import.meta.env.BASE_URL}black-cat-studio.svg`}
              alt="Black Cat Studio"
              style={{ width: "100%", height: "100%", position: "relative" }}
            />
          </div>
          <div style={{
            position: "absolute",
            bottom: 10,
            right: 118,
            fontSize: 10,
            color: "#2a2a3a",
            fontFamily: "'SF Mono', 'SF Pro Text', monospace",
            lineHeight: 1.5,
            textAlign: "right",
            pointerEvents: "none",
            userSelect: "none",
          }}>
            <div>{formattedDatetime}</div>
            <div>{totalNodes.toLocaleString()} nodes</div>
          </div>
        </div>

        {/* Sidebar */}
        <div style={{
          width: 380,
          borderLeft: "1px solid #1e2030",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}>
          {inFamilyFocus && hasContinentData && (
            <HabitatMap
              selectedContinents={selected?.continents ?? []}
              highlightedContinent={highlightedContinent}
              onContinentClick={c => setHighlightedContinent(prev => prev === c ? null : c)}
            />
          )}
          {selected && navContext && (
            <NodeNav
              parent={navContext.parent}
              siblings={navContext.siblings}
              index={navContext.index}
              onNavigate={handleSelect}
              breadcrumbPath={breadcrumbPath}
              colorTheme={colorTheme}
            />
          )}
          <div ref={sidebarScrollRef} style={{ flex: 1, overflowY: "auto" }}>
            <UnifiedInfoPanel
              node={selectedInTree}
              onSelect={handleSelect}
              findNodeById={findNodeById}
              onFocusFamily={slug => setFocus(slug)}
              focusedFamilySlug={focusedFamilySlug}
              subfamilies={subfamiliesForPanel}
            />
          </div>
        </div>
      </div>
      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
      {showDays && <InternationalDaysModal onClose={() => setShowDays(false)} onNavigate={slug => { setFocus(slug); setShowDays(false); }} />}
      {showSotd && speciesOfTheDay && (
        <SpeciesOfTheDayModal
          species={speciesOfTheDay}
          onClose={() => setShowSotd(false)}
          onNavigate={(slug, nodeId) => { navigateTo(slug, nodeId); setShowSotd(false); }}
        />
      )}
      {showEponyms && (
        <EponymModal
          data={annotatedData}
          onClose={() => setShowEponyms(false)}
          onNavigate={(slug, nodeId) => { navigateTo(slug, nodeId); setShowEponyms(false); }}
        />
      )}
      {showCoverage && (
        <CoverageModal
          data={annotatedData}
          onClose={() => setShowCoverage(false)}
          onFocusFamily={slug => { setFocus(slug); setShowCoverage(false); }}
          initialFamilySlug={focusedFamilySlug}
          initialClassId={focusedClassId}
        />
      )}
    </div>
  );
}
