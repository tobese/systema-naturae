import type { Kingdom } from "../types";
import { KINGDOM_INTROS } from "../kingdomIntros";

// A dedicated "title page" for a kingdom, shown before a reader descends
// into its Parts — the kingdom-level counterpart to ChapterPage.tsx's
// Part-intro header, but its own full page rather than a block above
// Chapter 1. Reachable today by clicking a kingdom's own header in
// TableOfContents.tsx (see App.tsx's "kingdomIntro" phase); this is the
// natural drop-in point for the split-view left/right shell later, where
// it becomes the right pane's default content for a selected kingdom.
export function KingdomIntroPage({ kingdom }: { kingdom: Kingdom }) {
  const paragraphs = KINGDOM_INTROS[kingdom];

  return (
    <article style={{ maxWidth: 680, margin: "0 auto", padding: "3rem 1.5rem 8rem" }}>
      <header style={{ textAlign: "center", marginBottom: "3rem" }}>
        <p
          style={{
            fontFamily: "var(--font-display)",
            fontStyle: "italic",
            color: "var(--ink-faint)",
            letterSpacing: "0.05em",
          }}
        >
          Kingdom
        </p>
        <h1 style={{ fontSize: "2.8rem", letterSpacing: "0.06em" }}>{kingdom}</h1>
        <div style={{ width: "70px", height: "1px", background: "var(--rule-gold)", margin: "1.75rem auto 0" }} />
      </header>

      {paragraphs.map((paragraph, i) => (
        <p key={i} style={{ fontSize: "1.1rem", lineHeight: 1.85, color: "var(--ink-soft)", marginBottom: "1.5rem" }}>
          {i === 0 ? (
            <>
              <span
                aria-hidden
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "3.6rem",
                  lineHeight: "2.6rem",
                  float: "left",
                  marginRight: "0.5rem",
                  marginTop: "0.4rem",
                  color: "var(--rule-gold)",
                }}
              >
                {paragraph.charAt(0)}
              </span>
              {paragraph.slice(1)}
            </>
          ) : (
            paragraph
          )}
        </p>
      ))}
    </article>
  );
}
