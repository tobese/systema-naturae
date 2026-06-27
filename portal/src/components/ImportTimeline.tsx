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

interface DayPoint {
  date: Date;
  speciesRunning: number;
}

const W = 700;
const H = 400;
const M = { top: 28, right: 20, bottom: 56, left: 56 };
const IW = W - M.left - M.right;
const IH = H - M.top - M.bottom;

export default function ImportTimeline() {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const raw = (importLog as ImportEvent[]).filter(d => d.speciesRunning > 0);
    if (raw.length === 0) return;

    const firstDate = new Date(raw[0].date);
    const origin = new Date(firstDate.getTime() - 24 * 60 * 60 * 1000);

    const events = [{ date: origin, speciesRunning: 0, speciesAdded: 0, nodes: 0, commit: "", message: "", families: [] as string[] } as ImportEvent, ...raw];

    const dayPoints: DayPoint[] = [];
    for (let i = 0; i < events.length - 1; i++) {
      const a = events[i];
      const b = events[i + 1];
      const aDate = new Date(a.date);
      const bDate = new Date(b.date);
      const daysDiff = Math.round((bDate.getTime() - aDate.getTime()) / (24 * 60 * 60 * 1000));
      const speciesDiff = b.speciesRunning - a.speciesRunning;
      const dailyRate = daysDiff > 0 ? speciesDiff / daysDiff : speciesDiff;
      for (let d = 0; d <= daysDiff; d++) {
        const pointDate = new Date(aDate.getTime() + d * 24 * 60 * 60 * 1000);
        const speciesRunning = a.speciesRunning + dailyRate * d;
        dayPoints.push({ date: pointDate, speciesRunning: Math.round(speciesRunning) });
      }
    }

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const defs = svg.append("defs");
    defs.append("linearGradient")
      .attr("id", "grad")
      .attr("x1", "0").attr("y1", "0").attr("x2", "0").attr("y2", "1")
      .selectAll("stop")
      .data([
        { offset: "0%", color: "#6a8aba" },
        { offset: "100%", color: "#6a8aba00" },
      ])
      .enter()
      .append("stop")
      .attr("offset", d => d.offset)
      .attr("stop-color", d => d.color);

    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);

    const xDomain = d3.extent(dayPoints, d => d.date) as [Date, Date];
    const x = d3.scaleTime().domain(xDomain).range([0, IW]);

    const maxSpecies = d3.max(dayPoints, d => d.speciesRunning)!;
    const ySpecies = d3.scaleLinear()
      .domain([0, maxSpecies * 1.05]).range([IH, 0]);

    g.append("g")
      .call(d3.axisLeft(ySpecies).ticks(6).tickSize(-IW).tickFormat(d3.format("~s")))
      .selectAll(".tick line")
      .attr("stroke", "#1e2030");

    g.append("g")
      .attr("transform", `translate(0,${IH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat("%b %d") as any))
      .selectAll("text")
      .attr("fill", "#666");

    g.append("text")
      .attr("x", -40).attr("y", 12)
      .attr("fill", "#444").attr("font-size", 10)
      .text("Species");

    const area = d3.area<DayPoint>()
      .x(d => x(d.date)).y0(IH).y1(d => ySpecies(d.speciesRunning));
    g.append("path").datum(dayPoints).attr("d", area)
      .attr("fill", "url(#grad)").attr("opacity", 0.35);

    const line = d3.line<DayPoint>()
      .x(d => x(d.date)).y(d => ySpecies(d.speciesRunning));
    g.append("path").datum(dayPoints).attr("d", line)
      .attr("fill", "none").attr("stroke", "#6a8aba").attr("stroke-width", 2);

    g.selectAll(".dot")
      .data(dayPoints.filter(d => d.date >= firstDate))
      .join("circle")
      .attr("cx", d => x(d.date)).attr("cy", d => ySpecies(d.speciesRunning))
      .attr("r", 2.5).attr("fill", "#6a8aba").attr("stroke", "#0f1117").attr("stroke-width", 1);

    const container = svgRef.current!.parentElement!;
    const tooltip = d3.select(container)
      .append("div")
      .style("position", "absolute").style("display", "none")
      .style("background", "#151725").style("border", "1px solid #2a2d45")
      .style("border-radius", "6px").style("padding", "12px 14px")
      .style("font-size", "11px").style("color", "#b0b0c8")
      .style("pointer-events", "none").style("z-index", "300")
      .style("max-width", "300px").style("line-height", "1.5");

    const eventsByDate = new Map(events.filter(e => e.speciesRunning > 0).map(e => [e.date.slice(0, 10), e]));

    g.selectAll(".dot")
      .on("mouseenter", function (_, d) {
        const dateStr = d.date.toISOString().slice(0, 10);
        const ev = eventsByDate.get(dateStr);
        d3.select(this).attr("r", 4).attr("stroke-width", 2);
        let html = `<div style="font-weight:600;color:#d0d0e0;margin-bottom:4px">${d.date.toLocaleDateString("en-GB", { month: "short", day: "numeric", year: "numeric" })}</div>`;
        html += `<div><b style="color:#6a8aba">${d.speciesRunning.toLocaleString()}</b> species total</div>`;
        if (ev) {
          html += `<div style="margin-top:4px"><b style="color:#8aba6a">+${ev.speciesAdded.toLocaleString()}</b> species this batch</div>`;
          html += `<div style="font-size:10px;color:#666;margin-top:2px">${ev.families.length} families</div>`;
        }
        tooltip.style("display", "block").html(html);
      })
      .on("mousemove", function (e: MouseEvent) {
        const rect = svgRef.current!.getBoundingClientRect();
        tooltip
          .style("left", `${e.clientX - rect.left + 14}px`)
          .style("top", `${e.clientY - rect.top - 10}px`);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("r", 2.5).attr("stroke-width", 1);
        tooltip.style("display", "none");
      });
  }, []);

  const data = (importLog as ImportEvent[]).filter(d => d.speciesRunning > 0);
  const totalSpecies = data.reduce((s, d) => Math.max(s, d.speciesRunning), 0);
  const totalEvents = data.length;

  return (
    <div style={{ padding: "20px 0" }}>
      <div style={{ display: "flex", gap: 24, marginBottom: 20, fontSize: 12 }}>
        <div>
          <div style={{ color: "#444", fontSize: 10, marginBottom: 2 }}>SPECIES</div>
          <div style={{ color: "#8aba6a", fontSize: 18, fontWeight: 600 }}>{totalSpecies.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: "#444", fontSize: 10, marginBottom: 2 }}>BATCHES</div>
          <div style={{ color: "#6a8aba", fontSize: 18, fontWeight: 600 }}>{totalEvents}</div>
        </div>
      </div>

      <div style={{ position: "relative" }}>
        <svg ref={svgRef} width={W} height={H} />
      </div>
    </div>
  );
}
