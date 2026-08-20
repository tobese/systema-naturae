import { useBookOptions } from "../hooks/useBookOptions";

export function Breadcrumb({
  partTitle,
  chapterTitle,
  onHome,
}: {
  partTitle?: string;
  chapterTitle?: string;
  onHome: () => void;
}) {
  const { showExtinct, toggleShowExtinct } = useBookOptions();

  return (
    <nav
      style={{
        maxWidth: 680,
        margin: "0 auto",
        padding: "1.5rem 1.5rem 0",
        fontSize: "0.8rem",
        letterSpacing: "0.05em",
        color: "var(--ink-faint)",
        textTransform: "uppercase",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "1rem",
      }}
    >
      <span>
        <button
          onClick={onHome}
          style={{ background: "none", border: "none", padding: 0, cursor: "pointer", color: "inherit" }}
        >
          Contents
        </button>
        {partTitle && <span> / {partTitle}</span>}
        {chapterTitle && <span> / {chapterTitle}</span>}
      </span>

      <label
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          cursor: "pointer",
          flexShrink: 0,
        }}
      >
        <span>Show extinct species</span>
        <span
          onClick={toggleShowExtinct}
          role="switch"
          aria-checked={showExtinct}
          style={{
            width: 30,
            height: 16,
            borderRadius: 8,
            border: "1px solid var(--rule-gold)",
            background: showExtinct ? "var(--rule-gold)" : "transparent",
            position: "relative",
            transition: "background 0.15s ease",
            flexShrink: 0,
          }}
        >
          <span
            style={{
              position: "absolute",
              top: 1,
              left: showExtinct ? 15 : 1,
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: showExtinct ? "var(--paper)" : "var(--rule-gold)",
              transition: "left 0.15s ease",
            }}
          />
        </span>
      </label>
    </nav>
  );
}
