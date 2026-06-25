import { useEffect, useRef, useCallback, useState } from "react";
import * as d3 from "d3";
import type { TaxonNode, ColorTheme } from "../types";

interface Props {
  data: TaxonNode;
  layout: "radial" | "vertical";
  onSelect: (node: TaxonNode | null) => void;
  selectedId: string | null;
  pendingZoomId: React.MutableRefObject<string | null>;
  highlightedNodeIds?: Set<string> | null;
  colorTheme: ColorTheme;
  specialNodeId?: string | string[];
  focusedFamilySlug?: string | null;
  focusedClassId?: string | null;
  collapseThreshold?: number;
  nodeScale?: number;
}

type AnnotatedNode = d3.HierarchyNode<TaxonNode> & { subfamily?: string };
type PNode = d3.HierarchyPointNode<TaxonNode>;
type PLink = d3.HierarchyPointLink<TaxonNode>;

const DURATION = 600;
const DURATION_EXIT = 250;

function annotateSubfamily(node: AnnotatedNode, sf?: string): void {
  const next = node.data.rank === "SUBFAMILY" ? node.data.name : sf;
  node.subfamily = next;
  node.children?.forEach(c => annotateSubfamily(c as AnnotatedNode, next));
}

function classColor(node: AnnotatedNode, theme: ColorTheme): string | undefined {
  const cls = node.data.className;
  if (cls && theme.classPalette?.base?.[cls]) return theme.classPalette.base[cls];
  return undefined;
}

function orderColor(node: AnnotatedNode, theme: ColorTheme): string | undefined {
  const cls = node.data.className;
  const ord = node.data.orderName;
  if (!cls || !ord) return undefined;
  const base = theme.classPalette?.base?.[cls];
  if (!base) return undefined;
  // Derive from class base by shifting lightness deterministically
  const hash = ord.split("").reduce((s, c) => s + c.charCodeAt(0), 0);
  const h = parseInt(base.slice(1, 3), 16);
  const s2 = parseInt(base.slice(3, 5), 16);
  const l = parseInt(base.slice(5, 7), 16);
  const shift = (hash % 30) - 15;
  const clamp = (n: number) => Math.max(0, Math.min(255, Math.round(n)));
  return "#" + [h, s2, l].map((v, i) => clamp(v + (i === 2 ? shift : 0)).toString(16).padStart(2, "0")).join("");
}

function edgeColor(node: AnnotatedNode, theme: ColorTheme): string {
  if (node.data.rank === "KINGDOM") return "#c8a84a";
  if (node.data.rank === "PHYLUM") return "#9a8858";
  if (node.data.rank === "CLASS") return classColor(node, theme) ?? "#666";
  if (node.data.rank === "ORDER") return orderColor(node, theme) ?? classColor(node, theme) ?? "#666";
  if (node.data.rank === "BREED_GROUP" || node.data.rank === "BREED") return theme.breedGroupColor;
  if (node.data.rank === "HYBRID_GROUP" || node.data.rank === "HYBRID") return theme.hybridColor;
  if (node.data.rank === "FAMILY") return classColor(node, theme) ?? "#666";
  if (node.data.rank === "SUBSPECIES") {
    const lineage = node.data.lineage ?? (node.parent as AnnotatedNode | undefined)?.data.lineage;
    return lineage && theme.lineageColors[lineage] ? theme.lineageColors[lineage] : "#555";
  }
  const lineage = node.data.lineage ?? (node.children?.[0] as AnnotatedNode | undefined)?.data.lineage;
  if (lineage && theme.lineageColors[lineage]) return theme.lineageColors[lineage];
  if (node.data.rank === "SUBFAMILY") return theme.subfamilyColors[node.data.name] ?? "#444";
  return theme.subfamilyColors[node.subfamily ?? ""] ?? "#444";
}

function fillColor(node: AnnotatedNode, theme: ColorTheme): string {
  if (node.data.rank === "KINGDOM") return "#c8a84a";
  if (node.data.rank === "PHYLUM") return "#9a8858";
  if (node.data.rank === "CLASS") return classColor(node, theme) ?? "#666";
  if (node.data.rank === "ORDER") return orderColor(node, theme) ?? classColor(node, theme) ?? "#666";
  if (node.data.rank === "FAMILY") return "#F5F5F5";
  if (node.data.rank === "TRIBE") return "#F5F5F5";
  if (node.data.rank === "SUBFAMILY") return theme.subfamilyColors[node.data.name] ?? "#888";
  if (node.data.rank === "BREED_GROUP") return theme.breedGroupColor;
  if (node.data.rank === "BREED") return `${theme.breedGroupColor}88`;
  if (node.data.rank === "HYBRID_GROUP") return theme.hybridColor;
  if (node.data.rank === "HYBRID") return theme.hybridColor;
  if (node.data.rank === "SUBSPECIES") {
    const lineage = node.data.lineage ?? (node.parent as AnnotatedNode | undefined)?.data.lineage;
    const alpha = node.data.accepted === false ? "33" : "55";
    return lineage && theme.lineageColors[lineage] ? `${theme.lineageColors[lineage]}${alpha}` : "#333";
  }
  const lineage = node.data.lineage ?? (node.children?.[0] as AnnotatedNode | undefined)?.data.lineage;
  if (lineage && theme.lineageColors[lineage]) {
    return node.data.rank === "SPECIES" ? `${theme.lineageColors[lineage]}99` : theme.lineageColors[lineage];
  }
  const sfColor = theme.subfamilyColors[(node as AnnotatedNode).subfamily ?? ""] ?? "#888";
  return node.data.rank === "SPECIES" ? `${sfColor}77` : sfColor;
}

function nodeR(d: d3.HierarchyNode<TaxonNode>, specialSet: Set<string> | null): number {
  if (d.data.rank === "KINGDOM") return 10;
  if (d.data.rank === "PHYLUM") return 9;
  if (d.data.rank === "CLASS") return 8;
  if (d.data.rank === "ORDER") return 7;
  if (d.data.rank === "FAMILY") return 5;
  if (d.data.rank === "SUBFAMILY") return 4;
  if (d.data.rank === "TRIBE") return 4;
  if (d.data.rank === "GENUS") return 3;
  if (d.data.rank === "HYBRID_GROUP") return 3;
  if (d.data.rank === "BREED_GROUP") return 2.5;
  if (d.data.rank === "HYBRID") return 2;
  if (d.data.rank === "BREED") return 2;
  if (d.data.rank === "SUBSPECIES") return 2;
  if (specialSet?.has(d.data.id)) return 3;
  return 1.5;
}

function displayLabel(node: TaxonNode): string {
  if (["KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY"].includes(node.rank)) {
    return node.commonName ?? node.name;
  }
  return node.name;
}

function childSummary(node: TaxonNode): string {
  const children = node.children ?? [];
  if (children.length === 0) return "";
  const counts: Record<string, number> = {};
  function walk(n: TaxonNode): void {
    for (const c of n.children ?? []) {
      counts[c.rank] = (counts[c.rank] || 0) + 1;
      walk(c);
    }
  }
  walk(node);
  const rankLabels: Record<string, string> = {
    PHYLUM: "phyla", CLASS: "classes", ORDER: "orders",
    FAMILY: "families", SUBFAMILY: "subfamilies", TRIBE: "tribes",
    GENUS: "genera", SPECIES: "species",
  };
  const parts: string[] = [];
  for (const [rank, count] of Object.entries(counts)) {
    parts.push(`${count} ${rankLabels[rank] ?? (rank.toLowerCase() + "s")}`);
  }
  return parts.join(" · ");
}

// After d3.tree() computes a balanced [0, 2π] layout, remap angles so
// descendants of the focused class take 65% of the circle and everything
// else 35%. Runs in-place on the HierarchyPointNode x values.
function remapAnglesForClass(nodes: PNode[], focusedClassId: string): void {
  const focused: PNode[] = [];
  const others: PNode[] = [];
  for (const d of nodes) {
    let n: PNode | null = d;
    let hit = false;
    while (n) { if (n.data.id === focusedClassId) { hit = true; break; } n = n.parent as PNode | null; }
    (hit ? focused : others).push(d);
  }
  if (focused.length === 0) return;

  const fMin = Math.min(...focused.map(d => d.x));
  const fMax = Math.max(...focused.map(d => d.x));
  const fSpan = fMax - fMin || 1;
  const oArr = others.map(d => d.x).sort((a, b) => a - b);
  const oMin = oArr[0] ?? 0;
  const oMax = oArr[oArr.length - 1] ?? (2 * Math.PI);
  const oSpan = oMax - oMin || 1;

  const ARC_FOCUS = 2 * Math.PI * 0.65;
  const ARC_OTHER = 2 * Math.PI * 0.35;
  focused.forEach(d => { d.x = ((d.x - fMin) / fSpan) * ARC_FOCUS; });
  others.forEach(d => { d.x = ARC_FOCUS + ((d.x - oMin) / oSpan) * ARC_OTHER; });
}

function TooltipBox({
  node, x, y, imgUrl, containerW,
}: { node: TaxonNode; x: number; y: number; imgUrl: string | null; containerW: number }) {
  const flipLeft = x > containerW - 220;
  const isSpecies = ["SPECIES", "SUBSPECIES", "BREED", "HYBRID"].includes(node.rank);

  function content() {
    if (isSpecies) {
      return (
        <>
          {imgUrl && (
            <img src={imgUrl} alt="" style={{ width: "100%", height: "auto", borderRadius: 5, display: "block", marginBottom: 8 }} />
          )}
          <div style={{ fontStyle: "italic", fontSize: 11, color: "#555", lineHeight: 1.3 }}>
            {node.name}
          </div>
          {node.commonName && (
            <div style={{ fontSize: 13, color: "#ddd", fontWeight: 500, marginTop: 3 }}>
              {node.commonName}
            </div>
          )}
          {node.namedAfter && (
            <div style={{ fontSize: 10, color: "#446655", marginTop: 6, fontStyle: "italic" }}>
              Named after {node.namedAfter}
            </div>
          )}
        </>
      );
    }

    const summary = childSummary(node);

    if (node.rank === "SUBFAMILY" || node.rank === "TRIBE") {
      return (
        <>
          <div style={{ fontSize: 13, color: "#ddd", fontWeight: 600 }}>
            {node.name}
          </div>
          {summary && (
            <div style={{ fontSize: 10, color: "#888", marginTop: 4 }}>
              {summary}
            </div>
          )}
        </>
      );
    }

    if (node.rank === "GENUS") {
      return (
        <>
          <div style={{ fontStyle: "italic", fontSize: 12, color: "#ddd", fontWeight: 500 }}>
            {node.name}
          </div>
          {node.commonName && (
            <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
              {node.commonName}
            </div>
          )}
          {summary && (
            <div style={{ fontSize: 10, color: "#888", marginTop: 4 }}>
              {summary}
            </div>
          )}
        </>
      );
    }

    // KINGDOM through FAMILY
    const desc = node.description
      ? node.description.slice(0, 100) + (node.description.length > 100 ? "…" : "")
      : "";
    return (
      <>
        <div style={{ fontSize: 13, color: "#ddd", fontWeight: 600 }}>
          {node.commonName ?? node.name}
        </div>
        {node.commonName && (
          <div style={{ fontStyle: "italic", fontSize: 11, color: "#555", marginTop: 2 }}>
            {node.name}
          </div>
        )}
        {desc && (
          <div style={{ fontSize: 10, color: "#888", marginTop: 4, lineHeight: 1.3 }}>
            {desc}
          </div>
        )}
        {summary && (
          <div style={{ fontSize: 10, color: "#888", marginTop: 4 }}>
            {summary}
          </div>
        )}
      </>
    );
  }

  return (
    <div style={{
      position: "absolute",
      left: flipLeft ? x - 196 : x + 16,
      top: y + 8,
      width: 180,
      background: "#13131f",
      border: "1px solid #252535",
      borderRadius: 8,
      padding: "10px 12px",
      pointerEvents: "none",
      zIndex: 10,
      boxShadow: "0 4px 24px rgba(0,0,0,0.7)",
    }}>
      {content()}
    </div>
  );
}

interface Setup {
  zoom: d3.ZoomBehavior<SVGSVGElement, unknown>;
  g: d3.Selection<SVGGElement, unknown, null, undefined>;
  gSpecial: d3.Selection<SVGGElement, unknown, null, undefined>;
  gLinks: d3.Selection<SVGGElement, unknown, null, undefined>;
  gNodes: d3.Selection<SVGGElement, unknown, null, undefined>;
}

export default function FamilyTree({
  data, layout, onSelect, selectedId, pendingZoomId,
  highlightedNodeIds, colorTheme, specialNodeId, focusedFamilySlug, focusedClassId,
  collapseThreshold = 99999, nodeScale = 1,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ node: TaxonNode; x: number; y: number; imgUrl: string | null } | null>(null);
  const thumbnailCache = useRef<Map<string, string | null>>(new Map());
  const setupRef = useRef<Setup | null>(null);
  const prevLayoutRef = useRef<"radial" | "vertical" | null>(null);
  const savedZoomRef = useRef<d3.ZoomTransform | null>(null);
  const prevTreeKeyRef = useRef<string>("root");

  const zoomAnchorRef = useRef<{ sx: number; sy: number } | null>(null);

  const attachTooltip = useCallback((
    sel: d3.Selection<SVGGElement, PNode, SVGGElement, unknown>,
  ) => {
    sel.on("mouseenter", (event: MouseEvent, d) => {
      const [mx, my] = d3.pointer(event, containerRef.current!);
      const hasCached = thumbnailCache.current.has(d.data.id);
      const imgUrl = hasCached ? (thumbnailCache.current.get(d.data.id) ?? null) : null;
      setTooltip({ node: d.data, x: mx, y: my, imgUrl });
      const speciesRanks = ["SPECIES", "SUBSPECIES", "BREED", "HYBRID"];
      if (!hasCached && speciesRanks.includes(d.data.rank)) {
        const title = (d.data.commonName ?? d.data.name).replace(/\s*\([^)]*\)/g, "").trim().replace(/ /g, "_");
        fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`)
          .then(r => r.ok ? r.json() : null)
          .then((json: { thumbnail?: { source: string } } | null) => {
            const url = json?.thumbnail?.source ?? null;
            thumbnailCache.current.set(d.data.id, url);
            setTooltip(prev => prev?.node.id === d.data.id ? { ...prev, imgUrl: url } : prev);
          })
          .catch(() => thumbnailCache.current.set(d.data.id, null));
      }
    })
    .on("mouseleave", () => setTooltip(null));
  }, []);

  const render = useCallback(() => {
    const svg = svgRef.current;
    const container = containerRef.current;
    if (!svg || !container) return;

    const specialSet: Set<string> | null = specialNodeId
      ? new Set(Array.isArray(specialNodeId) ? specialNodeId : [specialNodeId])
      : null;

    setTooltip(null);
    const W = container.clientWidth;
    const H = container.clientHeight;
    d3.select(svg).attr("width", W).attr("height", H);

    // ── Initialize persistent structure once ─────────────────────────────────
    if (!setupRef.current) {
      // Clear any orphaned DOM from a previous aborted init (StrictMode timing edge case)
      d3.select(svg).selectAll("*").remove();
      const defs = d3.select(svg).append("defs");
      const glowFilter = defs.append("filter").attr("id", "glow");
      glowFilter.append("feGaussianBlur").attr("stdDeviation", "3.5").attr("result", "coloredBlur");
      const merge = glowFilter.append("feMerge");
      merge.append("feMergeNode").attr("in", "coloredBlur");
      merge.append("feMergeNode").attr("in", "SourceGraphic");

      const g = d3.select(svg).append("g");
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 6])
        .on("zoom", e => g.attr("transform", e.transform.toString()));
      d3.select(svg).call(zoom);

      setupRef.current = {
        zoom,
        g,
        gSpecial: g.append("g").attr("class", "special-links"),
        gLinks: g.append("g").attr("class", "links").attr("fill", "none").attr("stroke-width", 1),
        gNodes: g.append("g").attr("class", "nodes"),
      };

      // Restore zoom saved from previous render, or center the tree on first init.
      // Without this, cleanup + re-init on every render dep change resets the viewport.
      const restoredZoom = savedZoomRef.current ?? d3.zoomIdentity.translate(W / 2, H / 2);
      savedZoomRef.current = null;
      d3.select(svg).call(zoom.transform, restoredZoom);
    }

    const { zoom, gSpecial, gLinks, gNodes } = setupRef.current;
    const layoutChanged = prevLayoutRef.current !== null && prevLayoutRef.current !== layout;
    prevLayoutRef.current = layout;

    // ── Prune: when a family or class is focused, collapse others ─────────────
    const prunedData: TaxonNode = (focusedFamilySlug || focusedClassId)
      ? (function prune(n: TaxonNode): TaxonNode {
          // Family focus: collapse other families
          if (focusedFamilySlug && n.rank === "FAMILY" && n.familySlug && n.familySlug !== focusedFamilySlug) {
            return { ...n, children: undefined };
          }
          // Class focus: collapse other classes (keep the focused class expanded)
          if (!focusedFamilySlug && focusedClassId && n.rank === "CLASS" && n.id !== focusedClassId) {
            return { ...n, children: undefined };
          }
          const next = (n.children ?? []).map(prune);
          return next.length ? { ...n, children: next } : n;
        })(data)
      : data;

    // ── Collapse large nodes (when not in family focus) ────────────────────────
    const localScale = nodeScale;
    const nr = (d: d3.HierarchyNode<TaxonNode>, s: Set<string> | null) => nodeR(d, s) * localScale;
    const thresh = collapseThreshold;
    function collapseNode(n: TaxonNode): TaxonNode {
      if (!n.children || n.children.length === 0) return n;
      if (n.children.length > thresh) {
        return { ...n, children: undefined, _collapsed: true, _childCount: n.children.length } as unknown as TaxonNode;
      }
      const next = n.children.map(collapseNode);
      return { ...n, children: next };
    }
    const collapsedData = collapseNode(prunedData);

    // ── Compute layout ────────────────────────────────────────────────────────
    const root = d3.hierarchy(collapsedData);
    annotateSubfamily(root as AnnotatedNode);

    let nodeTransform: (d: PNode) => string;
    let ptNode: PNode;
    let defaultTransform: d3.ZoomTransform;

    if (layout === "radial") {
      const isFocused = !!(focusedClassId || focusedFamilySlug);
      const radius = Math.min(W, H) * (isFocused ? 0.70 : 0.42);

      if (root.children) {
        const hybridGrp = root.children.find(c => c.data.rank === "HYBRID_GROUP");
        if (hybridGrp) {
          const others = root.children.filter(c => c.data.rank !== "HYBRID_GROUP");
          if (others.length >= 2) {
            const mid = Math.floor(others.length / 2);
            root.children = [...others.slice(0, mid), hybridGrp, ...others.slice(mid)];
          }
        }
      }

      d3.tree<TaxonNode>()
        .size([2 * Math.PI, radius])
        .separation((a, b) => {
          const isHybrid = (n: d3.HierarchyNode<TaxonNode>) =>
            n.data.rank === "HYBRID" || n.data.rank === "HYBRID_GROUP";
          const base = a.parent === b.parent ? 1 : 2;
          return (isHybrid(a) || isHybrid(b) ? base * 2.5 : base) / a.depth;
        })(root);

      ptNode = root as PNode;

      if (focusedClassId) {
        remapAnglesForClass(ptNode.descendants(), focusedClassId);
      }

      nodeTransform = (d: PNode) => {
        const angle = d.x - Math.PI / 2;
        return `translate(${d.y * Math.cos(angle)},${d.y * Math.sin(angle)})`;
      };
      defaultTransform = d3.zoomIdentity.translate(W / 2, H / 2);
    } else {
      const marginL = 20;
      const marginR = 180;
      const marginV = 20;
      const nodeCount = root.descendants().length;
      const totalH = Math.max(H - marginV * 2, nodeCount * 14);

      d3.tree<TaxonNode>().size([totalH, W - marginL - marginR])(root);

      ptNode = root as PNode;
      nodeTransform = (d: PNode) => `translate(${d.y},${d.x})`;
      defaultTransform = d3.zoomIdentity.translate(marginL, marginV + (H - (Math.max(H - marginV * 2, nodeCount * 14))) / 2);
    }

    const descendants = ptNode.descendants();
    const nodeOpacity = (d: PNode): number => {
      if (!highlightedNodeIds) return 1;
      const isLeaf = d.data.rank === "SPECIES" || d.data.rank === "BREED"
        || d.data.rank === "HYBRID" || d.data.rank === "SUBSPECIES";
      if (!isLeaf) return 1;
      return highlightedNodeIds.has(d.data.id) ? 1 : 0.1;
    };

    // Auto-fit zoom when tree structure changes and no pending zoom target.
    const treeKey = `${focusedClassId ?? "all"}:${focusedFamilySlug ?? "all"}`;
    const treeChanged = prevTreeKeyRef.current !== treeKey;
    prevTreeKeyRef.current = treeKey;
    const hasPendingZoom = pendingZoomId.current !== null;
    if (!hasPendingZoom && (layoutChanged || treeChanged)) {
      d3.select(svg).call(zoom.transform, defaultTransform);
    }

    // ── Links ─────────────────────────────────────────────────────────────────
    const linkKey = (d: PLink) => `${d.source.data.id}→${d.target.data.id}`;

    const linkPathFn = layout === "radial"
      ? d3.linkRadial<PLink, PNode>().angle(n => n.x).radius(n => n.y)
      : d3.linkHorizontal<PLink, PNode>().x(n => n.y).y(n => n.x);

    const linkSel = gLinks.selectAll<SVGPathElement, PLink>("path")
      .data(ptNode.links(), linkKey);

    linkSel.exit()
      .transition().duration(DURATION_EXIT)
      .attr("stroke-opacity", 0)
      .remove();

    const linkEnter = linkSel.enter()
      .append("path")
      .attr("stroke-opacity", 0)
      .attr("d", linkPathFn);

    linkEnter.merge(linkSel)
      .transition().duration(DURATION)
      .attr("stroke", d => edgeColor(d.target as AnnotatedNode, colorTheme))
      .attr("stroke-opacity", 0.5)
      .attr("d", linkPathFn);

    // ── Nodes ─────────────────────────────────────────────────────────────────
    const nodeKey = (d: PNode) => d.data.id;

    const nodeSel = gNodes.selectAll<SVGGElement, PNode>("g.tn")
      .data(descendants, nodeKey);

    // Exit: shrink toward parent
    nodeSel.exit<PNode>()
      .style("pointer-events", "none")
      .transition().duration(DURATION_EXIT)
      .style("opacity", 0)
      .attr("transform", (d: PNode) => nodeTransform(d.parent ?? d))
      .remove();

    // Enter: start at parent position
    const nodeEnter = nodeSel.enter()
      .append("g")
      .attr("class", "tn")
      .attr("data-id",   d => d.data.id)
      .attr("data-rank", d => d.data.rank)
      .attr("transform", (d: PNode) => nodeTransform(d.parent ?? d))
      .style("opacity", 0)
      .style("cursor", "pointer");

    // Glow ring — always present, opacity controlled by selectedId
    nodeEnter.append("circle")
      .attr("class", "glow-ring")
      .attr("r", d => nr(d, specialSet) + 6)
      .attr("fill", "none")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .attr("filter", "url(#glow)");

    // Subspecies hint ring — always present, opacity controlled
    nodeEnter.append("circle")
      .attr("class", "subsp-ring")
      .attr("r", d => nr(d, specialSet) + 4)
      .attr("fill", "none")
      .attr("stroke", "#888")
      .attr("stroke-width", 0.5)
      .attr("stroke-dasharray", "2 2");

    // Collapse indicator ring — visible for collapsed nodes
    nodeEnter.append("circle")
      .attr("class", "collapse-ring")
      .attr("r", d => nr(d, specialSet) + 3)
      .attr("fill", "none")
      .attr("stroke", "#c89860")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4 3")
      .attr("opacity", d => (d.data as any)._collapsed ? 0.8 : 0);

    // IUCN status ring — hidden by default, shown for species with iucnStatus
    nodeEnter.append("circle")
      .attr("class", "iucn-ring")
      .attr("r", d => nr(d, specialSet) + 2.5)
      .attr("fill", "none")
      .attr("stroke-width", 1.5);

    // Main circle
    nodeEnter.append("circle").attr("class", "main-circle");

    // Label
    nodeEnter.filter(d => d.data.rank !== "BREED")
      .append("text")
      .attr("dy", "0.32em")
      .style("pointer-events", "none");

    // Transparent hit target
    nodeEnter.append("circle")
      .attr("class", "hit")
      .attr("fill", "transparent")
      .attr("stroke", "none");

    attachTooltip(nodeEnter as d3.Selection<SVGGElement, PNode, SVGGElement, unknown>);

    const merged = nodeEnter.merge(nodeSel);

    // Update click handler (refreshes stale closures on every render)
    merged.on("click", (_, d) => {
      const cur = d3.zoomTransform(svg);
      if (layout === "radial") {
        const a = d.x - Math.PI / 2;
        zoomAnchorRef.current = { sx: d.y * Math.cos(a) * cur.k + cur.x, sy: d.y * Math.sin(a) * cur.k + cur.y };
      } else {
        zoomAnchorRef.current = { sx: d.y * cur.k + cur.x, sy: d.x * cur.k + cur.y };
      }
      onSelect(d.data);
    });

    // Animate position + opacity (instant on structure change to avoid layout-shift before zoom)
    merged.transition().duration(layoutChanged ? 0 : DURATION)
      .attr("transform", nodeTransform)
      .style("opacity", nodeOpacity);

    // Glow ring visibility
    merged.select<SVGCircleElement>("circle.glow-ring")
      .attr("r", d => nr(d, specialSet) + 6)
      .attr("opacity", d => d.data.id === selectedId ? 0.3 : 0);

    // Subspecies hint ring visibility (also used as permanent crown ring for KINGDOM)
    merged.select<SVGCircleElement>("circle.subsp-ring")
      .attr("r", d => nr(d, specialSet) + 4)
      .attr("stroke", d => d.data.rank === "KINGDOM" ? "#c8a84a" : "#888")
      .attr("stroke-width", d => d.data.rank === "KINGDOM" ? 1.5 : 0.5)
      .attr("stroke-dasharray", d => d.data.rank === "KINGDOM" ? null : "2 2")
      .attr("opacity", d => {
        if (d.data.rank === "KINGDOM") return 0.6;
        return d.data.rank === "SPECIES" && (d.data.subspeciesCount ?? 0) > 0 && !d.children ? 0.5 : 0;
      });

    // Collapse indicator ring
    merged.select<SVGCircleElement>("circle.collapse-ring")
      .attr("r", d => nr(d, specialSet) + 3)
      .attr("opacity", d => (d.data as any)._collapsed ? 0.8 : 0);

    // IUCN status ring visibility
    merged.select<SVGCircleElement>("circle.iucn-ring")
      .attr("r", d => nr(d, specialSet) + 2.5)
      .attr("stroke", d => {
        if (d.data.rank !== "SPECIES" || !d.data.iucnStatus) return "none";
        const colorMap: Record<string, string> = {
          EX: "#6B6B6B", EW: "#9C9C9C", CR: "#D82E2E", EN: "#E87030",
          VU: "#E8B820", NT: "#B8B820", LC: "#60B060", DD: "#8888A8", NE: "#AAAAAA",
        };
        return colorMap[d.data.iucnStatus] ?? "none";
      })
      .attr("opacity", d => d.data.rank === "SPECIES" && d.data.iucnStatus ? 0.7 : 0);

    // Main circle visual update
    merged.select<SVGCircleElement>("circle.main-circle")
      .attr("r", d => nr(d, specialSet))
      .attr("fill", d => fillColor(d as AnnotatedNode, colorTheme))
      .attr("stroke", d => {
        if (d.data.id === selectedId) return "#fff";
        if (specialSet?.has(d.data.id) && !d.children) return colorTheme.breedGroupColor;
        if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return "#777";
        return "none";
      })
      .attr("stroke-width", d => {
        if (d.data.id === selectedId) return 3;
        if (specialSet?.has(d.data.id) && !d.children) return 1.5;
        if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return 1;
        return 0;
      })
      .attr("stroke-dasharray", d =>
        d.data.rank === "SUBSPECIES" && d.data.accepted === false ? "2 1.5" : null)
      .attr("stroke-opacity", d =>
        d.data.rank === "SUBSPECIES" && d.data.accepted === false ? 0.6 : 1);

    // Text visual + positioning update
    if (layout === "radial") {
      merged.select<SVGTextElement>("text")
        .attr("x", d => d.x < Math.PI ? nr(d, specialSet) + 4 : -(nr(d, specialSet) + 4))
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")
        .text(d => displayLabel(d.data))
        .style("font-size", d => {
          if (d.data.rank === "KINGDOM") return "14px";
          if (d.data.rank === "PHYLUM") return "12px";
          if (d.data.rank === "CLASS") return "11px";
          if (d.data.rank === "ORDER") return "10px";
          if (d.data.rank === "FAMILY") return "9px";
          if (d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE") return "8px";
          if (d.data.rank === "SPECIES" || d.data.rank === "SUBSPECIES") return "7px";
          return "8px";
        })
        .style("font-style", d => ["GENUS", "SPECIES", "SUBSPECIES"].includes(d.data.rank) ? "italic" : "normal")
        .style("font-weight", "400")
        .style("fill", d => {
          if (d.data.rank === "KINGDOM") return "#c8a84a";
          if (d.data.rank === "BREED_GROUP")
            return colorTheme.lineageColors[d.data.lineage ?? ""] ?? colorTheme.breedGroupColor;
          if (d.data.rank === "HYBRID_GROUP" || d.data.rank === "HYBRID") return colorTheme.hybridColor;
          return "#ddd";
        })
        .style("fill-opacity", d => {
          if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return 0.4;
          if (d.data.rank === "SPECIES") return 0.55;
          return 1;
        });
    } else {
      merged.select<SVGTextElement>("text")
        .attr("x", d => (d.children && d.parent ? -(nr(d, specialSet) + 4) : nr(d, specialSet) + 4))
        .attr("text-anchor", d => (d.children && d.parent ? "end" : "start"))
        .text(d => displayLabel(d.data))
        .style("font-size", d => {
          if (d.data.rank === "KINGDOM") return "14px";
          if (d.data.rank === "PHYLUM") return "12px";
          if (d.data.rank === "CLASS") return "11px";
          if (d.data.rank === "ORDER") return "10px";
          if (d.data.rank === "FAMILY") return "9px";
          if (d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE") return "8px";
          if (d.data.rank === "SPECIES" || d.data.rank === "SUBSPECIES") return "7px";
          return "8px";
        })
        .style("font-style", d => ["GENUS", "SPECIES", "SUBSPECIES"].includes(d.data.rank) ? "italic" : "normal")
        .style("font-weight", "400")
        .style("fill", d => {
          if (d.data.rank === "KINGDOM") return "#c8a84a";
          if (d.data.rank === "BREED_GROUP")
            return colorTheme.lineageColors[d.data.lineage ?? ""] ?? colorTheme.breedGroupColor;
          if (d.data.rank === "HYBRID_GROUP" || d.data.rank === "HYBRID") return colorTheme.hybridColor;
          return "#ddd";
        })
        .style("fill-opacity", d => {
          if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return 0.4;
          if (d.data.rank === "SPECIES") return 0.55;
          return 1;
        });
    }

    // Hit target radius update
    merged.select<SVGCircleElement>("circle.hit")
      .attr("r", d => Math.max(nr(d, specialSet) + 8, 14));

    // ── Special links (hybrid cross-links + rex coat-type lines) ─────────────
    // Full redraw on every update (these are rare and don't need animated transitions)
    gSpecial.selectAll("*").remove();

    const posMap = new Map<string, { x: number; y: number }>();
    if (layout === "radial") {
      ptNode.descendants().forEach(d => {
        const angle = d.x - Math.PI / 2;
        posMap.set(d.data.id, { x: d.y * Math.cos(angle), y: d.y * Math.sin(angle) });
      });
    } else {
      ptNode.descendants().forEach(d => posMap.set(d.data.id, { x: d.y, y: d.x }));
    }

    const hybridLinks = ptNode.descendants()
      .filter(d => d.data.rank === "HYBRID" && d.data.hybridParents)
      .flatMap(d => (d.data.hybridParents!).map(pid => ({ hybrid: d, parentId: pid })));

    if (hybridLinks.length > 0) {
      type HybridDatum = { hybrid: PNode; parentId: string };
      const lineAttrs = (sel: d3.Selection<SVGLineElement, HybridDatum, SVGGElement, unknown>) =>
        sel
          .attr("x1", ({ parentId }) => posMap.get(parentId)?.x ?? 0)
          .attr("y1", ({ parentId }) => posMap.get(parentId)?.y ?? 0)
          .attr("x2", ({ hybrid }) => posMap.get(hybrid.data.id)?.x ?? 0)
          .attr("y2", ({ hybrid }) => posMap.get(hybrid.data.id)?.y ?? 0);

      lineAttrs(gSpecial.append("g").selectAll<SVGLineElement, HybridDatum>("line")
        .data(hybridLinks).join("line"))
        .attr("stroke", colorTheme.hybridColor).attr("stroke-opacity", 0.35)
        .attr("stroke-width", 1).attr("stroke-dasharray", "4 4")
        .style("pointer-events", "none");

      lineAttrs(gSpecial.append("g").selectAll<SVGLineElement, HybridDatum>("line")
        .data(hybridLinks).join("line"))
        .attr("stroke", "transparent").attr("stroke-width", 10)
        .style("cursor", "pointer")
        .on("click", (event, d) => { event.stopPropagation(); onSelect(d.hybrid.data); });
    }

    if (colorTheme.coatTypeColor) {
      const rexBreeds = ptNode.descendants()
        .filter(d => d.data.rank === "BREED" && d.data.coatType === "rex");
      const rexPairs: { a: PNode; b: PNode }[] = [];
      for (let i = 0; i < rexBreeds.length; i++)
        for (let j = i + 1; j < rexBreeds.length; j++)
          rexPairs.push({ a: rexBreeds[i], b: rexBreeds[j] });
      if (rexPairs.length > 0) {
        gSpecial.append("g").selectAll("line")
          .data(rexPairs).join("line")
          .attr("x1", ({ a }) => posMap.get(a.data.id)?.x ?? 0)
          .attr("y1", ({ a }) => posMap.get(a.data.id)?.y ?? 0)
          .attr("x2", ({ b }) => posMap.get(b.data.id)?.x ?? 0)
          .attr("y2", ({ b }) => posMap.get(b.data.id)?.y ?? 0)
          .attr("stroke", colorTheme.coatTypeColor)
          .attr("stroke-opacity", 0.35)
          .attr("stroke-width", 1)
          .attr("stroke-dasharray", "4 4");
      }
    }

    // ── Zoom ─────────────────────────────────────────────────────────────────
    if (layoutChanged) {
      d3.select(svg).transition().duration(DURATION)
        .call(zoom.transform, defaultTransform);
    }

    const zoomTarget = pendingZoomId.current;
    pendingZoomId.current = null;
    if (zoomTarget) {
      const target = ptNode.descendants().find(d => d.data.id === zoomTarget);
      if (target) {
        const scale = 2.4;
        let tx: number, ty: number;
        if (layout === "radial") {
          const angle = target.x - Math.PI / 2;
          tx = target.y * Math.cos(angle);
          ty = target.y * Math.sin(angle);
        } else {
          tx = target.y;
          ty = target.x;
        }

        // Keep the target node at its pre-click screen position while zooming
        // (anchor persists across Strict Mode double-render — never cleared)
        const anchor = zoomAnchorRef.current;
        let sx: number, sy: number;
        if (anchor) {
          sx = anchor.sx; sy = anchor.sy;
        } else {
          const cur = d3.zoomTransform(svg);
          sx = tx * cur.k + cur.x;
          sy = ty * cur.k + cur.y;
        }

        d3.select(svg).transition().duration(700).call(
          zoom.transform,
          d3.zoomIdentity.translate(sx - tx * scale, sy - ty * scale).scale(scale),
        );
      }
    }
  }, [data, layout, onSelect, selectedId, pendingZoomId, highlightedNodeIds, colorTheme, specialNodeId, focusedFamilySlug, focusedClassId, attachTooltip, nodeScale, collapseThreshold]);

  useEffect(() => {
    render();
    const ro = new ResizeObserver(render);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => {
      ro.disconnect();
      // Save zoom so the next render can restore it (cleanup runs on every dep change, not just unmount)
      if (svgRef.current && setupRef.current) {
        savedZoomRef.current = d3.zoomTransform(svgRef.current);
      }
    };
  }, [render]);

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", position: "relative" }}>
      <svg ref={svgRef} style={{ width: "100%", height: "100%", display: "block" }} />
      {tooltip && (
        <TooltipBox
          node={tooltip.node}
          x={tooltip.x}
          y={tooltip.y}
          imgUrl={tooltip.imgUrl}
          containerW={containerRef.current?.clientWidth ?? 800}
        />
      )}
    </div>
  );
}
