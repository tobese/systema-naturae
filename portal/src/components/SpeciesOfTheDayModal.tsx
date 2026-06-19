import { useEffect } from "react";
import type { SpeciesOfTheDay } from "../hooks/useSpeciesOfTheDay";

const CONTINENT_NAMES: Record<string, string> = {
  NA: "North America", SA: "South America", EU: "Europe",
  AF: "Africa", AS: "Asia", OC: "Oceania", AN: "Antarctica",
};

function continentLabel(codes: string[]): string {
  return codes.map(c => CONTINENT_NAMES[c] ?? c).join(", ");
}

interface Props {
  species: SpeciesOfTheDay;
  onClose: () => void;
  onNavigate: (slug: string, nodeId: string) => void;
}

export default function SpeciesOfTheDayModal({ species, onClose, onNavigate }: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); } };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const today = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

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
          borderRadius: 12,
          width: "100%",
          maxWidth: 480,
          position: "relative",
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

        <div style={{ padding: "28px 32px 32px" }}>
          <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 16 }}>
            Species of the Day · {today}
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 24, fontWeight: 600, color: "#e0e0e0", lineHeight: 1.2, marginBottom: 4 }}>
              {species.commonName ?? species.name}
            </div>
            <div style={{ fontSize: 14, color: "#666", fontStyle: "italic" }}>
              {species.name}
            </div>
          </div>

          {species.description && (
            <div style={{ fontSize: 13, color: "#999", lineHeight: 1.65, marginBottom: 20 }}>
              {species.description}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 7, marginBottom: 24 }}>
            {species.continents && species.continents.length > 0 && (
              <div style={{ fontSize: 12, color: "#555" }}>
                <span style={{ color: "#3a3d50", marginRight: 8 }}>Range</span>
                {continentLabel(species.continents)}
              </div>
            )}
            {species.subspeciesCount !== undefined && species.subspeciesCount > 0 && (
              <div style={{ fontSize: 12, color: "#555" }}>
                <span style={{ color: "#3a3d50", marginRight: 8 }}>Subspecies</span>
                {species.subspeciesCount}
              </div>
            )}
            {species.namedAfter && (
              <div style={{ fontSize: 12, color: "#555" }}>
                <span style={{ color: "#3a3d50", marginRight: 8 }}>Named after</span>
                {species.namedAfter}
              </div>
            )}
          </div>

          <button
            onClick={() => { onNavigate(species.familySlug, species.id); onClose(); }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "#1a1f2e",
              border: "1px solid #2a3040",
              borderRadius: 6,
              padding: "8px 14px",
              cursor: "pointer",
              fontSize: 12,
              color: "#9aaacc",
            }}
            onMouseEnter={e => { e.currentTarget.style.background = "#1e2436"; e.currentTarget.style.color = "#b8c8e8"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "#1a1f2e"; e.currentTarget.style.color = "#9aaacc"; }}
          >
            <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
            View in portal
          </button>
        </div>
      </div>
    </div>
  );
}
