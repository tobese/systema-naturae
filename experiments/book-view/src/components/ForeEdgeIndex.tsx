import { useEffect, useState } from "react";
import type { Kingdom } from "@shared/book/types";

export interface EdgeKingdomEntry {
  kingdom: Kingdom;
  color: string;
  classes: { className: string; title: string }[];
}

function scrollToId(id: string) {
  // Instant, not smooth: targets can be 60k+ px away in a 118-Part book,
  // where an animated scroll is just a multi-second wait for no benefit.
  document.getElementById(id)?.scrollIntoView({ behavior: "instant", block: "start" });
}

// Mimics a dictionary's fore-edge thumb index: one colored tab per kingdom,
// pinned where a real book's page edges would be. Clicking a tab scrolls the
// TOC to that kingdom and opens a flyout of its classes (the next rank down)
// for a direct jump.
export function ForeEdgeIndex({ entries }: { entries: EdgeKingdomEntry[] }) {
  const [expanded, setExpanded] = useState<Kingdom | null>(null);
  const [active, setActive] = useState<Kingdom | null>(null);

  useEffect(() => {
    const targets = entries
      .map((e) => document.getElementById(`kingdom-${e.kingdom}`))
      .filter((el): el is HTMLElement => el !== null);
    if (targets.length === 0) return;

    const observer = new IntersectionObserver(
      (observed) => {
        const visible = observed.filter((o) => o.isIntersecting);
        if (visible.length === 0) return;
        const topMost = visible.reduce((a, b) =>
          a.boundingClientRect.top < b.boundingClientRect.top ? a : b,
        );
        setActive(topMost.target.id.replace("kingdom-", "") as Kingdom);
      },
      { rootMargin: "-10% 0px -70% 0px" },
    );
    targets.forEach((t) => observer.observe(t));
    return () => observer.disconnect();
  }, [entries]);

  return (
    <div
      style={{
        position: "fixed",
        // Anchored to the TOC's page column (maxWidth 680, so 340 to its
        // right edge), not the browser viewport - on a wide window the
        // page edge is where the text ends, not out at the screen's edge.
        // The max(0px, ...) clamp keeps tabs on-screen if the window is
        // narrower than the column.
        right: "max(0px, calc(50% - 340px))",
        top: 0,
        width: "2.25rem",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-evenly",
        alignItems: "flex-end",
        padding: "3rem 0",
        // A gilt-edge band for the strip itself, so the space around/between
        // the kingdom tabs still reads as the book's page edge rather than
        // bare paper - a soft metallic sheen down the middle, like light
        // catching a gilded fore-edge.
        background:
          "linear-gradient(90deg, #6f5726 0%, #a3823a 25%, #e2c680 50%, #a3823a 75%, #6f5726 100%)",
        boxShadow: "inset 2px 0 6px rgba(0,0,0,0.25)",
        zIndex: 20,
      }}
    >
      {expanded && (
        // Click-outside-to-close: covers the whole viewport behind the tabs
        // and flyout (which paint after it, so stay clickable) - without it
        // an open flyout just sits there when you click into the content.
        <div
          onClick={() => setExpanded(null)}
          style={{ position: "fixed", inset: 0 }}
        />
      )}
      {entries.map((entry) => {
        const isActive = active === entry.kingdom;
        const isExpanded = expanded === entry.kingdom;
        return (
          <div key={entry.kingdom} style={{ position: "relative", width: "100%" }}>
            {isExpanded && (
              <div
                style={{
                  position: "absolute",
                  right: "100%",
                  top: 0,
                  marginRight: "0.5rem",
                  background: "var(--paper)",
                  border: `1px solid ${entry.color}`,
                  borderRadius: "4px",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
                  padding: "0.5rem",
                  maxHeight: "70vh",
                  overflowY: "auto",
                  width: "220px",
                }}
              >
                {entry.classes.map((c) => (
                  <button
                    key={c.className}
                    onClick={() => {
                      scrollToId(`class-${entry.kingdom}-${c.className}`);
                      setExpanded(null);
                    }}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      background: "none",
                      border: "none",
                      borderLeft: `3px solid ${entry.color}`,
                      padding: "0.35rem 0.5rem",
                      cursor: "pointer",
                      color: "var(--ink)",
                      fontSize: "0.8rem",
                      fontFamily: "var(--font-body)",
                    }}
                  >
                    {c.className}
                  </button>
                ))}
              </div>
            )}
            <button
              onClick={() => {
                setExpanded(isExpanded ? null : entry.kingdom);
                scrollToId(`kingdom-${entry.kingdom}`);
              }}
              title={entry.kingdom}
              style={{
                width: "100%",
                padding: "0.7rem 0.3rem",
                background: entry.color,
                border: "none",
                borderRadius: "6px 0 0 6px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: isActive ? "0 0 0 2px var(--paper), 0 0 0 3px var(--ink)" : "0 1px 4px rgba(0,0,0,0.3)",
                transform: isActive ? "translateX(-10px)" : "translateX(0)",
                transition: "transform 0.15s ease",
              }}
            >
              <span
                style={{
                  writingMode: "vertical-rl",
                  color: "var(--paper)",
                  fontSize: "0.72rem",
                  letterSpacing: "0.08em",
                  fontFamily: "var(--font-display)",
                  whiteSpace: "nowrap",
                }}
              >
                {entry.kingdom}
              </span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
