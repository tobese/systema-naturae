import { useRef, useEffect } from "react";
import * as d3 from "d3";
import importLog from "../../data/import-log.json";

interface ImportEvent {
  date: string;
  commit: string;
  message: string;
  families: string[];
  speciesAdded: number;
  speciesRunning: number;
  nodes: number;
}

const W = 700;
const H = 360;
const M = { top: 28, right: 20, bottom: 56, left: 56 };
const IW = W - M.left - M.right;
const IH = H - M.top - M.bottom;

export default function ImportTimeline() {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const data = (importLog as ImportEvent[]).filter(d => d.speciesRunning > 0);
    if (data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);

    const xDomain = d3.extent(data, d => new Date(d.date)) as [Date, Date];
    const x = d3.scaleTime().domain(xDomain).range([0, IW]);
    const ySpecies = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.speciesRunning)! * 1.05])
      .range([IH, 0]);
    const yBars = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.speciesAdded)! * 1.3])
      .range([IH, 0]);

    // Grid lines
    g.append("g")
      .call(d3.axisLeft(ySpecies).ticks(6).tickSize(-IW).tickFormat(d3.format("~s")))
      .selectAll(".tick line")
      .attr("stroke", "#1e2030");

    // X axis
    g.append("g")
      .attr("transform", `translate(0,${IH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat("%b %d") as any))
      .selectAll("text")
      .attr("fill", "#666");

    // Y axis label
    g.append("text")
      .attr("x", -40).attr("y", 12)
      .attr("fill", "#444").attr("font-size", 10)
      .text("Species");

    // Area — cumulative species
    const area = d3.area<ImportEvent>()
      .x(d => x(new Date(d.date)))
      .y0(IH)
      .y1(d => ySpecies(d.speciesRunning))
      .curve(d3.curveStepAfter);

    g.append("path")
      .datum(data)
      .attr("d", area)
      .attr("fill", "url(#grad)")
      .attr("opacity", 0.5);

    // Cumulative line
    const line = d3.line<ImportEvent>()
      .x(d => x(new Date(d.date)))
      .y(d => ySpecies(d.speciesRunning))
      .curve(d3.curveStepAfter);

    g.append("path")
      .datum(data)
      .attr("d", line)
      .attr("fill", "none")
      .attr("stroke", "#6a8aba")
      .attr("stroke-width", 2);

    // Bars — species per batch
    g.selectAll(".bar")
      .data(data)
      .join("rect")
      .attr("class", "bar")
      .attr("x", d => x(new Date(d.date)) + 2)
      .attr("width", Math.max(4, IW / data.length - 4))
      .attr("y", d => yBars(d.speciesAdded))
      .attr("height", d => IH - yBars(d.speciesAdded))
      .attr("fill", "#5a8aba")
      .attr("opacity", 0.6)
      .attr("rx", 2)
      .on("mouseenter", function (_, d) {
        d3.select(this).attr("opacity", 1);
        tooltip.style("display", "block").html(formatTooltip(d));
      })
      .on("mousemove", function (e: MouseEvent) {
        const rect = svgRef.current!.getBoundingClientRect();
        tooltip
          .style("left", `${e.clientX - rect.left + 14}px`)
          .style("top", `${e.clientY - rect.top - 10}px`);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("opacity", 0.6);
        tooltip.style("display", "none");
      });

    // Gradient def
    const defs = svg.select("defs");
    if (!defs.empty()) {
      defs.append("linearGradient")
        .attr("id", "grad")
        .attr("x1", "0").attr("y1", "0")
        .attr("x2", "0").attr("y2", "1")
        .selectAll("stop")
        .data([
          { offset: "0%", color: "#6a8aba" },
          { offset: "100%", color: "#6a8aba00" },
        ])
        .enter()
        .append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);
    }

    // Tooltip
    const tooltip = d3.select(svgRef.current!.parentElement!)
      .append("div")
      .attr("class", "import-tooltip")
      .style("position", "absolute")
      .style("display", "none")
      .style("background", "#151725")
      .style("border", "1px solid #2a2d45")
      .style("border-radius", "6px")
      .style("padding", "12px 14px")
      .style("font-size", "11px")
      .style("color", "#b0b0c8")
      .style("pointer-events", "none")
      .style("z-index", "300")
      .style("max-width", "300px")
      .style("line-height", "1.5");

    function formatTooltip(d: ImportEvent): string {
      const date = new Date(d.date).toLocaleDateString("en-GB", {
        month: "short", day: "numeric", year: "numeric",
      });
      const msg = d.message.length > 60 ? d.message.slice(0, 60) + "…" : d.message;
      const famList = d.families.length > 8
        ? d.families.slice(0, 8).join(", ") + ` +${d.families.length - 8} more`
        : d.families.join(", ");
      return `
        <div style="font-weight:600;color:#d0d0e0;margin-bottom:4px">${date}</div>
        <div style="margin-bottom:6px;font-size:10px;color:#666">${msg}</div>
        <div style="display:flex;gap:12px;margin-bottom:4px">
          <span><b style="color:#8aba6a">${d.speciesAdded.toLocaleString()}</b> species added</span>
          <span><b style="color:#6a8aba">${d.speciesRunning.toLocaleString()}</b> total species</span>
        </div>
        <div style="font-size:10px;color:#666">${famList}</div>
      `;
    }
  }, []);

  const totalEvents = (importLog as ImportEvent[]).filter(d => d.speciesRunning > 0).length;
  const totalSpecies = (importLog as ImportEvent[]).reduce((s, d) => Math.max(s, d.speciesRunning), 0);
  const totalFamilies = (importLog as ImportEvent[]).reduce((s, d) => Math.max(s, d.families.length), 0);

  return (
    <div style={{ padding: "20px 0" }}>
      {/* Summary stats */}
      <div style={{ display: "flex", gap: 24, marginBottom: 20, fontSize: 12 }}>
        <div>
          <div style={{ color: "#444", fontSize: 10, marginBottom: 2 }}>FAMILIES</div>
          <div style={{ color: "#d0d0e0", fontSize: 18, fontWeight: 600 }}>{totalFamilies}</div>
        </div>
        <div>
          <div style={{ color: "#444", fontSize: 10, marginBottom: 2 }}>SPECIES</div>
          <div style={{ color: "#8aba6a", fontSize: 18, fontWeight: 600 }}>{totalSpecies.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: "#444", fontSize: 10, marginBottom: 2 }}>IMPORT BATCHES</div>
          <div style={{ color: "#6a8aba", fontSize: 18, fontWeight: 600 }}>{totalEvents}</div>
        </div>
      </div>

      {/* Chart container */}
      <div style={{ position: "relative" }}>
        <svg ref={svgRef} width={W} height={H} />
      </div>
    </div>
  );
}
