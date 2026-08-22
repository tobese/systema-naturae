import { OptionsPanel } from "./OptionsPanel";

export function Breadcrumb({
  partTitle,
  chapterTitle,
  onHome,
}: {
  partTitle?: string;
  chapterTitle?: string;
  onHome: () => void;
}) {
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

      <OptionsPanel />
    </nav>
  );
}
