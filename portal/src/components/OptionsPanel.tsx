import { useState } from "react";

export interface PortalOptions {
  showExtinct: boolean;
  collapseLarge: boolean;
  collapseThreshold: number;
}

interface Props {
  options: PortalOptions;
  onChange: (opts: PortalOptions) => void;
}

export default function OptionsPanel({ options, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const toggle = (key: keyof PortalOptions) => {
    if (key === "collapseThreshold") return;
    onChange({ ...options, [key]: !(options as any)[key] });
  };

  return (
    <div style={{ position: "relative" }}>
      {/* Gear button */}
      <button
        onClick={() => setOpen(!open)}
        title="Options"
        style={{
          width: 32,
          height: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "transparent",
          border: "none",
          color: open ? "#c0c0d8" : "#555",
          fontSize: 18,
          cursor: "pointer",
          borderRadius: 4,
          transition: "color 0.15s",
        }}
        onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
        onMouseLeave={e => (e.currentTarget.style.color = open ? "#c0c0d8" : "#555")}
      >
        ⚙
      </button>

      {/* Flyout panel */}
      {open && (
        <>
          {/* Overlay to catch clicks outside */}
          <div
            onClick={() => setOpen(false)}
            style={{ position: "fixed", inset: 0, zIndex: 199 }}
          />
          <div
            style={{
              position: "absolute",
              top: "100%",
              right: 0,
              marginTop: 4,
              background: "#151725",
              border: "1px solid #2a2d45",
              borderRadius: 8,
              padding: "14px 16px",
              zIndex: 200,
              minWidth: 200,
              fontSize: 12,
              lineHeight: 1.8,
            }}
          >
            <div style={{ color: "#6666aa", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
              Display options
            </div>

            <LabelRow checked={options.showExtinct} onChange={() => toggle("showExtinct")}>
              Show extinct species
            </LabelRow>

            <LabelRow checked={options.collapseLarge} onChange={() => toggle("collapseLarge")}>
              Collapse large nodes ({options.collapseThreshold}+)
            </LabelRow>
          </div>
        </>
      )}
    </div>
  );
}

function LabelRow({ checked, onChange, children }: { checked: boolean; onChange: () => void; children: React.ReactNode }) {
  return (
    <div
      onClick={onChange}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        cursor: "pointer",
        padding: "4px 0",
        color: "#a0a8b8",
      }}
      onMouseEnter={e => (e.currentTarget.style.color = "#d0d0e0")}
      onMouseLeave={e => (e.currentTarget.style.color = "#a0a8b8")}
    >
      <span style={{
        width: 14,
        height: 14,
        borderRadius: 3,
        border: "1px solid #3a3d55",
        background: checked ? "#6a8aba" : "transparent",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        fontSize: 10,
        color: "#fff",
      }}>
        {checked ? "✓" : ""}
      </span>
      {children}
    </div>
  );
}
