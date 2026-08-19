import type { BookNode } from "../types";

export function SpeciesEntry({ species }: { species: BookNode }) {
  const hasContent = Boolean(species.description || species.namedAfter || species.continents?.length);
  const dagger = species.extinct || species.fossil ? "† " : "";

  return (
    <div style={{ padding: "0.85rem 0", borderBottom: "1px solid var(--paper-shadow)" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.6rem", flexWrap: "wrap" }}>
        <span style={{ fontFamily: "var(--font-display)", fontStyle: "italic", fontSize: "1.05rem" }}>
          {dagger}
          {species.name}
        </span>
        {species.commonName && (
          <span style={{ fontSize: "0.9rem", color: "var(--ink-soft)" }}>{species.commonName}</span>
        )}
        {typeof species.subspeciesCount === "number" && species.subspeciesCount > 0 && (
          <span style={{ fontSize: "0.75rem", color: "var(--ink-faint)" }}>
            ({species.subspeciesCount} subspecies)
          </span>
        )}
      </div>

      {species.description && (
        <p style={{ margin: "0.4rem 0 0", fontSize: "0.95rem", lineHeight: 1.6, color: "var(--ink-soft)" }}>
          {species.description}
        </p>
      )}

      {species.namedAfter && (
        <p style={{ margin: "0.3rem 0 0", fontSize: "0.85rem", fontStyle: "italic", color: "var(--ink-faint)" }}>
          Named in honor of {species.namedAfter}.
        </p>
      )}

      {species.continents && species.continents.length > 0 && (
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginTop: "0.4rem" }}>
          {species.continents.map((c) => (
            <span
              key={c}
              style={{
                fontSize: "0.7rem",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                color: "var(--ink-faint)",
                border: "1px solid var(--paper-shadow)",
                borderRadius: "2px",
                padding: "0.1rem 0.4rem",
              }}
            >
              {c}
            </span>
          ))}
        </div>
      )}

      {!hasContent && (
        <p style={{ margin: "0.3rem 0 0", fontSize: "0.8rem", fontStyle: "italic", color: "var(--ink-faint)" }}>
          not yet described here
        </p>
      )}
    </div>
  );
}
