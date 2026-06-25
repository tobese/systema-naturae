import { useState, useEffect, useCallback, useMemo } from "react";
import type { TaxonNode } from "@shared/types";
import { CLASS_PALETTE } from "../colors";

interface Props {
  data: TaxonNode;
  onClose: () => void;
  onNavigate: (slug: string | null, nodeId: string) => void;
}

const SECTOR_COUNT = 12;
const SECTOR_ANGLE = 360 / SECTOR_COUNT;

function getClasses(root: TaxonNode): { name: string; color: string; node: TaxonNode }[] {
  const classes: { name: string; color: string; node: TaxonNode }[] = [];
  for (const phylum of root.children ?? []) {
    for (const cls of phylum.children ?? []) {
      if (cls.rank === "CLASS") {
        classes.push({
          name: cls.commonName ?? cls.name,
          color: CLASS_PALETTE[cls.name.toLowerCase()] ?? "#888",
          node: cls,
        });
      }
    }
  }
  return classes;
}

function collectSpecies(node: TaxonNode): TaxonNode[] {
  if (node.rank === "SPECIES") return [node];
  return (node.children ?? []).flatMap(collectSpecies);
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const angleRad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function describeSector(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`;
}

export default function WheelOfNature({ data, onClose, onNavigate }: Props) {
  const classes = useMemo(() => getClasses(data), [data]);
  const [rotation, setRotation] = useState(0);
  const [isSpinning, setIsSpinning] = useState(false);
  const [winner, setWinner] = useState<{ className: string; species: TaxonNode } | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const spin = useCallback(() => {
    if (isSpinning) return;
    setIsSpinning(true);
    setWinner(null);

    const spins = 5 + Math.floor(Math.random() * 3);
    const extraDeg = Math.random() * 360;
    const finalRotation = rotation + spins * 360 + extraDeg;
    setRotation(finalRotation);

    setTimeout(() => {
      const effectiveAngle = (360 - (finalRotation % 360)) % 360;
      const sectorIndex = Math.floor(effectiveAngle / SECTOR_ANGLE) % SECTOR_COUNT;
      const winningClass = classes[sectorIndex];
      const speciesList = collectSpecies(winningClass.node);
      const randomSpecies = speciesList[Math.floor(Math.random() * speciesList.length)];
      setWinner({ className: winningClass.name, species: randomSpecies ?? winningClass.node });
      setIsSpinning(false);
    }, 4000);
  }, [isSpinning, rotation, classes]);

  const goToSpecies = useCallback(() => {
    if (!winner) return;
    onNavigate(winner.species.familySlug ?? null, winner.species.id);
    onClose();
  }, [winner, onNavigate, onClose]);

  const wheelRadius = 160;
  const cx = 200;
  const cy = 200;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.8)",
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
          borderRadius: 16,
          width: "100%",
          maxWidth: 520,
          position: "relative",
          padding: "32px",
          textAlign: "center",
        }}
      >
        <button
          onClick={onClose}
          title="Close"
          style={{
            position: "absolute",
            top: 12,
            right: 14,
            width: 28,
            height: 28,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "transparent",
            border: "none",
            color: "#444",
            fontSize: 18,
            cursor: "pointer",
            borderRadius: 4,
          }}
          onMouseEnter={e => { e.currentTarget.style.color = "#aaa"; }}
          onMouseLeave={e => { e.currentTarget.style.color = "#444"; }}
        >
          ×
        </button>

        <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 20 }}>
          Wheel of Nature
        </div>

        <div style={{ position: "relative", width: 400, height: 400, margin: "0 auto" }}>
          <svg width={400} height={400} viewBox="0 0 400 400">
            <g
              style={{
                transformOrigin: `${cx}px ${cy}px`,
                transition: isSpinning ? "transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)" : "none",
                transform: `rotate(${rotation}deg)`,
              }}
            >
              {classes.map((cls, i) => {
                const startAngle = i * SECTOR_ANGLE;
                const endAngle = (i + 1) * SECTOR_ANGLE;
                const midAngle = startAngle + SECTOR_ANGLE / 2;
                const labelPos = polarToCartesian(cx, cy, wheelRadius * 0.65, midAngle);
                return (
                  <g key={cls.name}>
                    <path
                      d={describeSector(cx, cy, wheelRadius, startAngle, endAngle)}
                      fill={cls.color + "33"}
                      stroke={cls.color + "66"}
                      strokeWidth={1}
                    />
                    <text
                      x={labelPos.x}
                      y={labelPos.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#ccc"
                      fontSize={10}
                      fontWeight={500}
                      style={{ pointerEvents: "none" }}
                    >
                      {cls.name}
                    </text>
                  </g>
                );
              })}
              <circle cx={cx} cy={cy} r={18} fill="#0f1117" stroke="#2a3040" strokeWidth={2} />
              <circle cx={cx} cy={cy} r={6} fill="#555" />
            </g>

            {Array.from({ length: SECTOR_COUNT }).map((_, i) => {
              const angle = i * SECTOR_ANGLE;
              const pos = polarToCartesian(cx, cy, wheelRadius + 6, angle);
              return (
                <circle key={i} cx={pos.x} cy={pos.y} r={3} fill="#555" />
              );
            })}

            <g transform={`translate(${cx}, ${cy - wheelRadius - 24})`}>
              <path d="M -8 0 L 8 0 L 0 20 Z" fill="#c8a84a" stroke="#a08030" strokeWidth={1} />
              <circle cx={0} cy={0} r={5} fill="#c8a84a" stroke="#a08030" strokeWidth={1} />
            </g>
          </svg>
        </div>

        {winner && (
          <div style={{ marginTop: 20, padding: "14px 18px", background: "#11131a", borderRadius: 10, border: "1px solid #1e2030" }}>
            <div style={{ fontSize: 11, color: "#555", marginBottom: 6 }}>
              Winner from <span style={{ color: "#aaa" }}>{winner.className}</span>
            </div>
            <div style={{ fontSize: 20, fontWeight: 600, color: "#e0e0e0", fontStyle: "italic", marginBottom: 4 }}>
              {winner.species.name}
            </div>
            {winner.species.commonName && (
              <div style={{ fontSize: 14, color: "#888", marginBottom: 12 }}>{winner.species.commonName}</div>
            )}
            <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
              <button
                onClick={goToSpecies}
                style={{
                  background: "#1a1f2e",
                  border: "1px solid #2a3040",
                  borderRadius: 6,
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontSize: 12,
                  color: "#9aaacc",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#1e2436"; e.currentTarget.style.color = "#b8c8e8"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#1a1f2e"; e.currentTarget.style.color = "#9aaacc"; }}
              >
                View species
              </button>
              <button
                onClick={spin}
                style={{
                  background: "#1a2a1e",
                  border: "1px solid #2a4030",
                  borderRadius: 6,
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontSize: 12,
                  color: "#8aaa8a",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#1e3224"; e.currentTarget.style.color = "#a0c8a0"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#1a2a1e"; e.currentTarget.style.color = "#8aaa8a"; }}
              >
                Spin again
              </button>
            </div>
          </div>
        )}

        {!winner && (
          <button
            onClick={spin}
            disabled={isSpinning}
            style={{
              marginTop: 24,
              background: isSpinning ? "#151725" : "#1a1f2e",
              border: "1px solid #2a3040",
              borderRadius: 8,
              padding: "10px 28px",
              cursor: isSpinning ? "default" : "pointer",
              fontSize: 14,
              fontWeight: 500,
              color: isSpinning ? "#555" : "#9aaacc",
              letterSpacing: "0.04em",
            }}
            onMouseEnter={e => { if (!isSpinning) { e.currentTarget.style.background = "#1e2436"; e.currentTarget.style.color = "#b8c8e8"; }}}
            onMouseLeave={e => { if (!isSpinning) { e.currentTarget.style.background = "#1a1f2e"; e.currentTarget.style.color = "#9aaacc"; }}}
          >
            {isSpinning ? "Spinning..." : "Spin the wheel"}
          </button>
        )}
      </div>
    </div>
  );
}
