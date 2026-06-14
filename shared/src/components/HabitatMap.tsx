import { useMemo, useRef, useEffect } from "react";
import * as d3 from "d3";
import continentsData from "../data/continents.json";

const W = 300;
const H = 153;

const CONTINENT_COLORS: Record<string, string> = {
  "Africa":        "#C87941",
  "Asia":          "#2E9E8C",
  "Europe":        "#5B8DD9",
  "North America": "#7B6FA0",
  "South America": "#E05C5C",
};

const LABEL_POSITIONS: Record<string, [number, number]> = {
  "Africa":        [17, 0],
  "Asia":          [90, 40],
  "Europe":        [15, 54],
  "North America": [-100, 48],
  "South America": [-58, -15],
};

interface Props {
  selectedContinents: string[];
  highlightedContinent: string | null;
  onContinentClick: (c: string | null) => void;
}

export default function HabitatMap({ selectedContinents, highlightedContinent, onContinentClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  const projection = useMemo(() => {
    return d3.geoNaturalEarth1()
      .scale(46)
      .translate([W / 2, H / 2 + 4]);
  }, []);

  const pathGen = useMemo(() => d3.geoPath(projection), [projection]);

  useEffect(() => {
    const svg = d3.select(svgRef.current!);
    svg.selectAll("*").remove();

    svg.append("rect")
      .attr("width", W).attr("height", H)
      .attr("fill", "transparent")
      .style("cursor", "default")
      .on("click", () => onContinentClick(null));

    const features = (continentsData as GeoJSON.FeatureCollection).features;

    features.forEach(feature => {
      const name = (feature.properties as { name: string }).name;
      const baseColor = CONTINENT_COLORS[name] ?? "#888";
      const isSelected = selectedContinents.includes(name);
      const isHighlighted = highlightedContinent === name;
      const isActive = isSelected || isHighlighted;

      const g = svg.append("g");

      g.append("path")
        .datum(feature)
        .attr("d", pathGen as never)
        .attr("fill", baseColor)
        .attr("fill-opacity", isActive ? (isHighlighted ? 0.85 : 0.65) : 0.15)
        .attr("stroke", isHighlighted ? baseColor : baseColor)
        .attr("stroke-opacity", isActive ? 0.7 : 0.25)
        .attr("stroke-width", isHighlighted ? 1.5 : 0.5)
        .style("cursor", "pointer")
        .style("transition", "fill-opacity 0.2s, stroke-opacity 0.2s")
        .on("click", (event) => {
          event.stopPropagation();
          onContinentClick(name);
        });

      const labelPos = LABEL_POSITIONS[name];
      if (labelPos) {
        const [lx, ly] = projection(labelPos as [number, number]) ?? [0, 0];
        const shortName = name === "North America" ? "N. America" :
                          name === "South America" ? "S. America" : name;
        g.append("text")
          .attr("x", lx).attr("y", ly)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "middle")
          .attr("font-size", 7)
          .attr("font-family", "'SF Pro Text', system-ui, sans-serif")
          .attr("fill", isActive ? "#fff" : "#666")
          .attr("fill-opacity", isActive ? 0.9 : 0.7)
          .style("pointer-events", "none")
          .style("user-select", "none")
          .text(shortName);
      }
    });
  }, [projection, pathGen, selectedContinents, highlightedContinent, onContinentClick]);

  return (
    <div style={{
      borderBottom: "1px solid #1e2030",
      flexShrink: 0,
      background: "#0a0c12",
    }}>
      <div style={{ padding: "8px 12px 4px", fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", color: "#444" }}>
        Habitat
      </div>
      <svg
        ref={svgRef}
        width={W}
        height={H}
        style={{ display: "block" }}
      />
    </div>
  );
}
