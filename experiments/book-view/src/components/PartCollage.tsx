import type { CollageEntry } from "../types";

// A 9x9 plate of representative species for a Part's intro, shown once
// above "Chapter 1" alongside the Class-level description (see
// ChapterPage.tsx's showPartIntro block). Candidates are pre-selected in
// extractSlice.ts (collectCollageCandidates + buildCollage) - only species
// with both a real description and a portrait image. Flagship classes
// (see src/collageOverrides.ts) pin specific species at specific slots -
// e.g. Mammalia centers Homo sapiens - everything else, and every class
// without an override, is a deterministic even sample across the whole
// class so a Part with hundreds of families doesn't just show whichever
// family happens to come first alphabetically.
export function PartCollage({ items }: { items: CollageEntry[] }) {
  if (items.length === 0) return null;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(9, 1fr)",
        gap: "0.35rem",
        maxWidth: 620,
        margin: "1.75rem auto 2.25rem",
      }}
    >
      {items.map((item) => (
        <figure key={item.name} title={item.commonName || item.name} style={{ margin: 0, minWidth: 0 }}>
          <img
            src={item.imageUrl}
            alt={item.commonName || item.name}
            loading="lazy"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).closest("figure")!.style.display = "none";
            }}
            style={{
              width: "100%",
              aspectRatio: "1 / 1",
              objectFit: "contain",
              background: "var(--paper-shadow)",
              borderRadius: "2px",
              border: "1px solid var(--paper-shadow)",
              display: "block",
            }}
          />
          <figcaption
            style={{
              marginTop: "0.2rem",
              fontSize: "0.55rem",
              fontStyle: "italic",
              color: "var(--ink-faint)",
              lineHeight: 1.2,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {item.commonName || item.name}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
