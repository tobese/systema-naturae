import { useState } from "react";
import { useBookOptions } from "../hooks/useBookOptions";

// Mirrors the portal's own ⚙ OptionsPanel (gear button -> dropdown of
// checkbox rows) for a consistent pattern across the two apps, restyled for
// book-view's paper palette instead of the portal's dark dashboard one.
export function OptionsPanel() {
  const [open, setOpen] = useState(false);
  const { showExtinct, toggleShowExtinct, showStubs, toggleShowStubs, showEmptyFamilies, toggleShowEmptyFamilies } =
    useBookOptions();

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        title="Options"
        style={{
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          color: open ? "var(--rule-gold)" : "var(--ink-faint)",
          fontSize: "1rem",
          lineHeight: 1,
        }}
      >
        ⚙
      </button>

      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 9 }} />
          <div
            style={{
              position: "absolute",
              top: "100%",
              right: 0,
              marginTop: "0.5rem",
              background: "var(--paper)",
              border: "1px solid var(--paper-shadow)",
              borderRadius: "4px",
              boxShadow: "0 4px 16px rgba(42,33,24,0.18)",
              padding: "0.75rem 1rem",
              zIndex: 10,
              minWidth: 220,
              fontSize: "0.8rem",
              textTransform: "none",
              letterSpacing: "normal",
            }}
          >
            <OptionRow checked={showExtinct} onChange={toggleShowExtinct}>
              Show extinct species
            </OptionRow>
            <OptionRow checked={showStubs} onChange={toggleShowStubs}>
              Show stub species
            </OptionRow>
            <OptionRow checked={showEmptyFamilies} onChange={toggleShowEmptyFamilies}>
              Show empty families
            </OptionRow>
          </div>
        </>
      )}
    </div>
  );
}

function OptionRow({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: () => void;
  children: React.ReactNode;
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
        cursor: "pointer",
        padding: "0.4rem 0",
        color: "var(--ink-soft)",
      }}
    >
      <span>{children}</span>
      <span
        onClick={onChange}
        role="switch"
        aria-checked={checked}
        style={{
          width: 30,
          height: 16,
          borderRadius: 8,
          border: "1px solid var(--rule-gold)",
          background: checked ? "var(--rule-gold)" : "transparent",
          position: "relative",
          transition: "background 0.15s ease",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 1,
            left: checked ? 15 : 1,
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: checked ? "var(--paper)" : "var(--rule-gold)",
            transition: "left 0.15s ease",
          }}
        />
      </span>
    </label>
  );
}
