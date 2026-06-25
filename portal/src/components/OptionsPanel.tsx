import { useState } from "react";

export interface PortalOptions {
  showExtinct: boolean;
  collapseLarge: boolean;
  collapseThreshold: number;
  nodeScale: number;
  highlightWikipedia: boolean;
}

interface Props {
  options: PortalOptions;
  onChange: (opts: PortalOptions) => void;
}

export default function OptionsPanel({ options, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const toggle = (key: keyof PortalOptions) => {
    if (key === "collapseThreshold" || key === "nodeScale") return;
    onChange({ ...options, [key]: !(options as any)[key] });
  };

  const setNum = (key: "collapseThreshold" | "nodeScale", val: number) => {
    onChange({ ...options, [key]: val });
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen(!open)}
        title="Options"
        style={{
          width: 32, height: 32,
          display: "flex", alignItems: "center", justifyContent: "center",
          background: "transparent", border: "none",
          color: open ? "#c0c0d8" : "#555",
          fontSize: 18, cursor: "pointer", borderRadius: 4,
          transition: "color 0.15s",
        }}
        onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
        onMouseLeave={e => (e.currentTarget.style.color = open ? "#c0c0d8" : "#555")}
      >
        ⚙
      </button>

      {open && (
        <>
          <div onClick={() => setOpen(false)}
            style={{ position: "fixed", inset: 0, zIndex: 199 }} />
          <div style={{
            position: "absolute", top: "100%", right: 0, marginTop: 4,
            background: "#151725", border: "1px solid #2a2d45", borderRadius: 8,
            padding: "14px 16px", zIndex: 200, minWidth: 220, fontSize: 12, lineHeight: 1.8,
          }}>
            <div style={{ color: "#6666aa", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
              Display options
            </div>

            <LabelRow checked={options.showExtinct} onChange={() => toggle("showExtinct")}>
              Show extinct species
            </LabelRow>

            <LabelRow checked={options.highlightWikipedia} onChange={() => toggle("highlightWikipedia")}>
              Highlight Wikipedia species
            </LabelRow>

            <LabelRow checked={options.collapseLarge} onChange={() => toggle("collapseLarge")}>
              Collapse large nodes
            </LabelRow>

            {options.collapseLarge && (
              <SliderRow value={options.collapseThreshold} min={3} max={80}
                label="Threshold"
                onChange={v => setNum("collapseThreshold", v)} />
            )}

            <SliderRow value={options.nodeScale} min={0.5} max={2.0} step={0.1}
              label="Node scale"
              onChange={v => setNum("nodeScale", Math.round(v * 10) / 10)} />
          </div>
        </>
      )}
    </div>
  );
}

function LabelRow({ checked, onChange, children }: { checked: boolean; onChange: () => void; children: React.ReactNode }) {
  return (
    <div onClick={onChange} style={{
      display: "flex", alignItems: "center", gap: 8, cursor: "pointer", padding: "4px 0", color: "#a0a8b8",
    }}
      onMouseEnter={e => (e.currentTarget.style.color = "#d0d0e0")}
      onMouseLeave={e => (e.currentTarget.style.color = "#a0a8b8")}
    >
      <span style={{
        width: 14, height: 14, borderRadius: 3, border: "1px solid #3a3d55",
        background: checked ? "#6a8aba" : "transparent",
        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        fontSize: 10, color: "#fff",
      }}>
        {checked ? "✓" : ""}
      </span>
      {children}
    </div>
  );
}

function SliderRow({ value, min, max, step, label, onChange }: {
  value: number; min: number; max: number; step?: number; label: string; onChange: (v: number) => void;
}) {
  return (
    <div style={{ padding: "6px 0 4px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", color: "#777", fontSize: 10, marginBottom: 2 }}>
        <span>{label}</span>
        <span style={{ color: "#a0a8b8" }}>{value}{step && step < 1 ? "×" : ""}</span>
      </div>
      <input type="range" min={min} max={max} step={step ?? 1} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: "100%", accentColor: "#6a8aba", height: 4, cursor: "pointer" }} />
    </div>
  );
}
