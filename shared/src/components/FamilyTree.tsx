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
}

type AnnotatedNode = d3.HierarchyNode<TaxonNode> & { subfamily?: string };

function annotateSubfamily(node: AnnotatedNode, sf?: string): void {
  const next = node.data.rank === "SUBFAMILY" ? node.data.name : sf;
  node.subfamily = next;
  node.children?.forEach(c => annotateSubfamily(c as AnnotatedNode, next));
}

function edgeColor(node: AnnotatedNode, theme: ColorTheme): string {
  if (node.data.rank === "BREED_GROUP" || node.data.rank === "BREED") return theme.breedGroupColor;
  if (node.data.rank === "HYBRID_GROUP" || node.data.rank === "HYBRID") return theme.hybridColor;
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
  if (node.data.rank === "FAMILY" || node.data.rank === "TRIBE") return "#F5F5F5";
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
  const sfColor = theme.subfamilyColors[node.subfamily ?? ""] ?? "#888";
  return node.data.rank === "SPECIES" ? `${sfColor}77` : sfColor;
}

function nodeR(d: d3.HierarchyNode<TaxonNode>, specialSet: Set<string> | null): number {
  if (d.data.rank === "FAMILY") return 9;
  if (d.data.rank === "SUBFAMILY") return 7;
  if (d.data.rank === "TRIBE") return 7;
  if (d.data.rank === "GENUS") return 5;
  if (d.data.rank === "HYBRID_GROUP") return 5;
  if (d.data.rank === "BREED_GROUP") return 4;
  if (d.data.rank === "HYBRID") return 3.5;
  if (d.data.rank === "BREED") return 2.5;
  if (d.data.rank === "SUBSPECIES") return 2.5;
  if (specialSet?.has(d.data.id)) return 4.5;
  return 3;
}

const TOOLTIP_RANKS = new Set(["SPECIES", "SUBSPECIES", "BREED", "HYBRID"]);

function TooltipBox({
  node, x, y, imgUrl, containerW,
}: { node: TaxonNode; x: number; y: number; imgUrl: string | null; containerW: number }) {
  const flipLeft = x > containerW - 220;
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
      {imgUrl && (
        <img
          src={imgUrl}
          alt=""
          style={{ width: "100%", height: "auto", borderRadius: 5, display: "block", marginBottom: 8 }}
        />
      )}
      <div style={{ fontStyle: "italic", fontSize: 11, color: "#555", lineHeight: 1.3 }}>
        {node.name}
      </div>
      {node.commonName && (
        <div style={{ fontSize: 13, color: "#ddd", fontWeight: 500, marginTop: 3 }}>
          {node.commonName}
        </div>
      )}
    </div>
  );
}

export default function FamilyTree({ data, layout, onSelect, selectedId, pendingZoomId, highlightedNodeIds, colorTheme, specialNodeId }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ node: TaxonNode; x: number; y: number; imgUrl: string | null } | null>(null);
  const thumbnailCache = useRef<Map<string, string | null>>(new Map());

  const attachTooltip = useCallback((nodeG: d3.Selection<SVGGElement, d3.HierarchyPointNode<TaxonNode>, SVGGElement, unknown>) => {
    nodeG
      .filter(d => TOOLTIP_RANKS.has(d.data.rank))
      .on("mouseenter", (event: MouseEvent, d) => {
        const [mx, my] = d3.pointer(event, containerRef.current!);
        const hasCached = thumbnailCache.current.has(d.data.id);
        const imgUrl = hasCached ? (thumbnailCache.current.get(d.data.id) ?? null) : null;
        setTooltip({ node: d.data, x: mx, y: my, imgUrl });
        if (!hasCached) {
          const title = (d.data.commonName ?? d.data.name).replace(/ /g, "_");
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
    d3.select(svg).selectAll("*").remove();
    d3.select(svg).attr("width", W).attr("height", H);

    const root = d3.hierarchy(data);
    annotateSubfamily(root as AnnotatedNode);

    const defs = d3.select(svg).append("defs");
    const glowFilter = defs.append("filter").attr("id", "glow");
    glowFilter.append("feGaussianBlur").attr("stdDeviation", "3.5").attr("result", "coloredBlur");
    const merge = glowFilter.append("feMerge");
    merge.append("feMergeNode").attr("in", "coloredBlur");
    merge.append("feMergeNode").attr("in", "SourceGraphic");

    const g = d3.select(svg).append("g");

    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 6])
      .on("zoom", e => g.attr("transform", e.transform.toString()));
    d3.select(svg).call(zoomBehavior);

    if (layout === "radial") {
      const radius = Math.min(W, H) * 0.42;

      // Place any HYBRID_GROUP between other subfamily children
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

      const ptNode = root as d3.HierarchyPointNode<TaxonNode>;

      g.append("g").attr("fill", "none").attr("stroke-width", 1)
        .selectAll("path")
        .data(ptNode.links())
        .join("path")
        .attr("stroke", d => edgeColor(d.target as AnnotatedNode, colorTheme))
        .attr("stroke-opacity", 0.5)
        .attr("d", d3.linkRadial<
          d3.HierarchyPointLink<TaxonNode>,
          d3.HierarchyPointNode<TaxonNode>
        >().angle(n => n.x).radius(n => n.y));

      const nodeG = g.append("g")
        .selectAll<SVGGElement, d3.HierarchyPointNode<TaxonNode>>("g")
        .data(ptNode.descendants())
        .join("g")
        .attr("transform", d => {
          const angle = d.x - Math.PI / 2;
          const x = d.y * Math.cos(angle);
          const y = d.y * Math.sin(angle);
          return `translate(${x},${y})`;
        })
        .style("cursor", "pointer")
        .style("opacity", d => {
          if (!highlightedNodeIds) return 1;
          const isLeaf = d.data.rank === "SPECIES" || d.data.rank === "BREED" || d.data.rank === "HYBRID" || d.data.rank === "SUBSPECIES";
          if (!isLeaf) return 1;
          return highlightedNodeIds.has(d.data.id) ? 1 : 0.1;
        })
        .on("click", (_, d) => onSelect(d.data));

      attachTooltip(nodeG);

      nodeG.filter(d => d.data.id === selectedId)
        .append("circle")
        .attr("r", d => nodeR(d, specialSet) + 6)
        .attr("fill", "none")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .attr("opacity", 0.3)
        .attr("filter", "url(#glow)");

      nodeG.filter(d =>
        d.data.rank === "SPECIES" &&
        (d.data.subspeciesCount ?? 0) > 0 &&
        !d.children
      ).append("circle")
        .attr("r", d => nodeR(d, specialSet) + 4)
        .attr("fill", "none")
        .attr("stroke", "#888")
        .attr("stroke-width", 0.5)
        .attr("stroke-dasharray", "2 2")
        .attr("opacity", 0.5);

      nodeG.append("circle")
        .attr("r", d => nodeR(d, specialSet))
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
        .attr("stroke-dasharray", d => d.data.rank === "SUBSPECIES" && d.data.accepted === false ? "2 1.5" : null)
        .attr("stroke-opacity", d => d.data.rank === "SUBSPECIES" && d.data.accepted === false ? 0.6 : 1);

      nodeG.filter(d => d.data.rank !== "BREED")
        .append("text")
        .attr("dy", "0.32em")
        .attr("x", d => d.x < Math.PI ? nodeR(d, specialSet) + 4 : -(nodeR(d, specialSet) + 4))
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")
        .text(d => d.data.commonName ?? d.data.name)
        .style("font-size", d => {
          if (d.data.rank === "FAMILY" || d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE") return "13px";
          if (d.data.rank === "SPECIES" || d.data.rank === "SUBSPECIES") return "8px";
          return "10px";
        })
        .style("font-style", d => ["GENUS", "SPECIES", "SUBSPECIES"].includes(d.data.rank) ? "italic" : "normal")
        .style("font-weight", d => d.data.rank === "FAMILY" || d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE" ? "600" : "400")
        .style("fill", d => {
          if (d.data.rank === "BREED_GROUP") return colorTheme.lineageColors[d.data.lineage ?? ""] ?? colorTheme.breedGroupColor;
          if (d.data.rank === "HYBRID_GROUP" || d.data.rank === "HYBRID") return colorTheme.hybridColor;
          return "#ddd";
        })
        .style("fill-opacity", d => {
          if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return 0.4;
          if (d.data.rank === "SPECIES") return 0.55;
          return 1;
        })
        .style("pointer-events", "none");

      nodeG.append("circle")
        .attr("r", d => Math.max(nodeR(d, specialSet) + 8, 14))
        .attr("fill", "transparent")
        .attr("stroke", "none");

      const posMap = new Map<string, { x: number; y: number }>();
      ptNode.descendants().forEach(d => {
        const angle = d.x - Math.PI / 2;
        posMap.set(d.data.id, { x: d.y * Math.cos(angle), y: d.y * Math.sin(angle) });
      });

      const hybridLinks = ptNode.descendants()
        .filter(d => d.data.rank === "HYBRID" && d.data.hybridParents)
        .flatMap(d => (d.data.hybridParents!).map(pid => ({ hybrid: d, parentId: pid })));
      {
        const hybridEdgeGroup = g.insert("g", ":first-child");
        const lineAttrs = (sel: d3.Selection<SVGLineElement, { hybrid: d3.HierarchyPointNode<TaxonNode>; parentId: string }, SVGGElement, unknown>) =>
          sel
            .attr("x1", ({ parentId }) => posMap.get(parentId)?.x ?? 0)
            .attr("y1", ({ parentId }) => posMap.get(parentId)?.y ?? 0)
            .attr("x2", ({ hybrid }) => posMap.get(hybrid.data.id)?.x ?? 0)
            .attr("y2", ({ hybrid }) => posMap.get(hybrid.data.id)?.y ?? 0);
        lineAttrs(hybridEdgeGroup.append("g").selectAll("line").data(hybridLinks).join<SVGLineElement>("line"))
          .attr("stroke", colorTheme.hybridColor).attr("stroke-opacity", 0.35)
          .attr("stroke-width", 1).attr("stroke-dasharray", "4 4")
          .style("pointer-events", "none");
        lineAttrs(hybridEdgeGroup.append("g").selectAll("line").data(hybridLinks).join<SVGLineElement>("line"))
          .attr("stroke", "transparent").attr("stroke-width", 10)
          .style("cursor", "pointer")
          .on("click", (event, d) => { event.stopPropagation(); onSelect(d.hybrid.data); });
      }

      if (colorTheme.coatTypeColor) {
        const rexBreeds = ptNode.descendants()
          .filter(d => d.data.rank === "BREED" && d.data.coatType === "rex");
        const rexPairs: { a: (typeof rexBreeds)[0]; b: (typeof rexBreeds)[0] }[] = [];
        for (let i = 0; i < rexBreeds.length; i++)
          for (let j = i + 1; j < rexBreeds.length; j++)
            rexPairs.push({ a: rexBreeds[i], b: rexBreeds[j] });
        if (rexPairs.length > 0) {
          g.insert("g", ":first-child")
            .selectAll("line")
            .data(rexPairs)
            .join("line")
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

      d3.select(svg).call(
        zoomBehavior.transform,
        d3.zoomIdentity.translate(W / 2, H / 2)
      );

      const zoomTarget = pendingZoomId.current;
      if (zoomTarget) {
        pendingZoomId.current = null;
        const target = ptNode.descendants().find(d => d.data.id === zoomTarget);
        if (target) {
          const angle = target.x - Math.PI / 2;
          const tx = target.y * Math.cos(angle);
          const ty = target.y * Math.sin(angle);
          const scale = 2.4;
          d3.select(svg).transition().duration(700).call(
            zoomBehavior.transform,
            d3.zoomIdentity.translate(W / 2 - tx * scale, H / 2 - ty * scale).scale(scale)
          );
        }
      }

    } else {
      const marginL = 20;
      const marginR = 180;
      const marginV = 20;
      const nodeCount = root.descendants().length;
      const totalH = Math.max(H - marginV * 2, nodeCount * 14);

      d3.tree<TaxonNode>()
        .size([totalH, W - marginL - marginR])(root);

      const ptNode = root as d3.HierarchyPointNode<TaxonNode>;

      g.append("g").attr("fill", "none").attr("stroke-width", 1)
        .selectAll("path")
        .data(ptNode.links())
        .join("path")
        .attr("stroke", d => edgeColor(d.target as AnnotatedNode, colorTheme))
        .attr("stroke-opacity", 0.5)
        .attr("d", d3.linkHorizontal<
          d3.HierarchyPointLink<TaxonNode>,
          d3.HierarchyPointNode<TaxonNode>
        >().x(n => n.y).y(n => n.x));

      const nodeG = g.append("g")
        .selectAll<SVGGElement, d3.HierarchyPointNode<TaxonNode>>("g")
        .data(ptNode.descendants())
        .join("g")
        .attr("transform", d => `translate(${d.y},${d.x})`)
        .style("cursor", "pointer")
        .style("opacity", d => {
          if (!highlightedNodeIds) return 1;
          const isLeaf = d.data.rank === "SPECIES" || d.data.rank === "BREED" || d.data.rank === "HYBRID" || d.data.rank === "SUBSPECIES";
          if (!isLeaf) return 1;
          return highlightedNodeIds.has(d.data.id) ? 1 : 0.1;
        })
        .on("click", (_, d) => onSelect(d.data));

      attachTooltip(nodeG);

      nodeG.filter(d => d.data.id === selectedId)
        .append("circle")
        .attr("r", d => nodeR(d, specialSet) + 6)
        .attr("fill", "none")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .attr("opacity", 0.3)
        .attr("filter", "url(#glow)");

      nodeG.filter(d =>
        d.data.rank === "SPECIES" &&
        (d.data.subspeciesCount ?? 0) > 0 &&
        !d.children
      ).append("circle")
        .attr("r", d => nodeR(d, specialSet) + 4)
        .attr("fill", "none")
        .attr("stroke", "#888")
        .attr("stroke-width", 0.5)
        .attr("stroke-dasharray", "2 2")
        .attr("opacity", 0.5);

      nodeG.append("circle")
        .attr("r", d => nodeR(d, specialSet))
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
        .attr("stroke-dasharray", d => d.data.rank === "SUBSPECIES" && d.data.accepted === false ? "2 1.5" : null)
        .attr("stroke-opacity", d => d.data.rank === "SUBSPECIES" && d.data.accepted === false ? 0.6 : 1);

      nodeG.append("text")
        .attr("dy", "0.32em")
        .attr("x", d => (d.children && d.parent ? -(nodeR(d, specialSet) + 4) : nodeR(d, specialSet) + 4))
        .attr("text-anchor", d => (d.children && d.parent ? "end" : "start"))
        .text(d => d.data.commonName ?? d.data.name)
        .style("font-size", d => {
          if (d.data.rank === "FAMILY" || d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE") return "13px";
          if (d.data.rank === "SPECIES" || d.data.rank === "SUBSPECIES") return "8px";
          return "10px";
        })
        .style("font-style", d => ["GENUS", "SPECIES", "SUBSPECIES"].includes(d.data.rank) ? "italic" : "normal")
        .style("font-weight", d => d.data.rank === "FAMILY" || d.data.rank === "SUBFAMILY" || d.data.rank === "TRIBE" ? "600" : "400")
        .style("fill", d => {
          if (d.data.rank === "BREED_GROUP") return colorTheme.lineageColors[d.data.lineage ?? ""] ?? colorTheme.breedGroupColor;
          if (d.data.rank === "HYBRID_GROUP" || d.data.rank === "HYBRID") return colorTheme.hybridColor;
          return "#ddd";
        })
        .style("fill-opacity", d => {
          if (d.data.rank === "SUBSPECIES" && d.data.accepted === false) return 0.4;
          if (d.data.rank === "SPECIES") return 0.55;
          return 1;
        })
        .style("pointer-events", "none");

      nodeG.append("circle")
        .attr("r", d => Math.max(nodeR(d, specialSet) + 8, 14))
        .attr("fill", "transparent")
        .attr("stroke", "none");

      const posMapV = new Map<string, { x: number; y: number }>();
      ptNode.descendants().forEach(d => posMapV.set(d.data.id, { x: d.y, y: d.x }));

      const hybridLinksV = ptNode.descendants()
        .filter(d => d.data.rank === "HYBRID" && d.data.hybridParents)
        .flatMap(d => (d.data.hybridParents!).map(pid => ({ hybrid: d, parentId: pid })));
      {
        const hybridEdgeGroupV = g.insert("g", ":first-child");
        const lineAttrsV = (sel: d3.Selection<SVGLineElement, { hybrid: d3.HierarchyPointNode<TaxonNode>; parentId: string }, SVGGElement, unknown>) =>
          sel
            .attr("x1", ({ parentId }) => posMapV.get(parentId)?.x ?? 0)
            .attr("y1", ({ parentId }) => posMapV.get(parentId)?.y ?? 0)
            .attr("x2", ({ hybrid }) => posMapV.get(hybrid.data.id)?.x ?? 0)
            .attr("y2", ({ hybrid }) => posMapV.get(hybrid.data.id)?.y ?? 0);
        lineAttrsV(hybridEdgeGroupV.append("g").selectAll("line").data(hybridLinksV).join<SVGLineElement>("line"))
          .attr("stroke", colorTheme.hybridColor).attr("stroke-opacity", 0.35)
          .attr("stroke-width", 1).attr("stroke-dasharray", "4 4")
          .style("pointer-events", "none");
        lineAttrsV(hybridEdgeGroupV.append("g").selectAll("line").data(hybridLinksV).join<SVGLineElement>("line"))
          .attr("stroke", "transparent").attr("stroke-width", 10)
          .style("cursor", "pointer")
          .on("click", (event, d) => { event.stopPropagation(); onSelect(d.hybrid.data); });
      }

      if (colorTheme.coatTypeColor) {
        const rexBreedsV = ptNode.descendants()
          .filter(d => d.data.rank === "BREED" && d.data.coatType === "rex");
        const rexPairsV: { a: (typeof rexBreedsV)[0]; b: (typeof rexBreedsV)[0] }[] = [];
        for (let i = 0; i < rexBreedsV.length; i++)
          for (let j = i + 1; j < rexBreedsV.length; j++)
            rexPairsV.push({ a: rexBreedsV[i], b: rexBreedsV[j] });
        if (rexPairsV.length > 0) {
          g.insert("g", ":first-child")
            .selectAll("line")
            .data(rexPairsV)
            .join("line")
            .attr("x1", ({ a }) => posMapV.get(a.data.id)?.x ?? 0)
            .attr("y1", ({ a }) => posMapV.get(a.data.id)?.y ?? 0)
            .attr("x2", ({ b }) => posMapV.get(b.data.id)?.x ?? 0)
            .attr("y2", ({ b }) => posMapV.get(b.data.id)?.y ?? 0)
            .attr("stroke", colorTheme.coatTypeColor)
            .attr("stroke-opacity", 0.35)
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "4 4");
        }
      }

      d3.select(svg).call(
        zoomBehavior.transform,
        d3.zoomIdentity.translate(marginL, marginV + (H - totalH) / 2)
      );

      const zoomTarget = pendingZoomId.current;
      if (zoomTarget) {
        pendingZoomId.current = null;
        const target = ptNode.descendants().find(d => d.data.id === zoomTarget);
        if (target) {
          const scale = 2.4;
          d3.select(svg).transition().duration(700).call(
            zoomBehavior.transform,
            d3.zoomIdentity.translate(W / 2 - target.y * scale, H / 2 - target.x * scale).scale(scale)
          );
        }
      }
    }
  }, [data, layout, onSelect, selectedId, pendingZoomId, highlightedNodeIds, colorTheme, specialNodeId, attachTooltip]);

  useEffect(() => {
    render();
    const ro = new ResizeObserver(render);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
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
