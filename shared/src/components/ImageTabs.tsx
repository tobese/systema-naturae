/**
 * ImageTabs — tabbed image slot for species panels.
 *
 * Shows a portrait by default. If a range map is also available, surfaces a
 * second tab. The range `<img>` is only mounted while its tab is active so
 * we don't pay for the (often 0.5–3 MB) Commons SVG until the user asks.
 *
 * When only one of the two images exists, no tab bar is rendered and the
 * single image is shown directly. When neither exists, returns null.
 */
import { useEffect, useState } from "react";

interface Props {
  portrait?: string;
  rangeMap?: string;
  alt: string;
  loading?: boolean;
  accent?: string;
}

type Tab = "photo" | "range";

export default function ImageTabs({ portrait, rangeMap, alt, loading, accent = "#8899bb" }: Props) {
  const [tab, setTab] = useState<Tab>(portrait ? "photo" : "range");

  // Reset to the default tab when the subject changes.
  useEffect(() => {
    setTab(portrait ? "photo" : "range");
  }, [portrait, rangeMap]);

  if (loading) {
    return (
      <div style={{
        marginTop: 16, width: "100%", height: 200,
        background: "#1a1a2a", borderRadius: 6,
      }} />
    );
  }

  if (!portrait && !rangeMap) return null;

  const both = !!portrait && !!rangeMap;

  return (
    <div style={{ marginTop: 16 }}>
      {both && (
        <div style={{
          display: "flex", gap: 0, marginBottom: 8,
          borderBottom: "1px solid #1a1a2a",
        }}>
          <TabBtn label="Photo" active={tab === "photo"} accent={accent} onClick={() => setTab("photo")} />
          <TabBtn label="Range" active={tab === "range"} accent={accent} onClick={() => setTab("range")} />
        </div>
      )}
      {portrait && (tab === "photo" || !both) && (
        <img
          src={portrait}
          alt={alt}
          style={{ width: "100%", height: "auto", borderRadius: 6, display: "block" }}
        />
      )}
      {rangeMap && (tab === "range" || !both) && (
        <img
          src={rangeMap}
          alt={`${alt} — range map`}
          style={{
            width: "100%", height: "auto", borderRadius: 6, display: "block",
            background: "#f5f5f5", // many IUCN range SVGs assume a light background
          }}
        />
      )}
    </div>
  );
}

function TabBtn({ label, active, accent, onClick }: {
  label: string;
  active: boolean;
  accent: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: "none",
        border: "none",
        borderBottom: `2px solid ${active ? accent : "transparent"}`,
        padding: "6px 12px",
        color: active ? accent : "#666",
        fontSize: 11,
        fontWeight: 500,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        cursor: "pointer",
        marginBottom: "-1px",
        transition: "color 120ms, border-color 120ms",
      }}
    >
      {label}
    </button>
  );
}
