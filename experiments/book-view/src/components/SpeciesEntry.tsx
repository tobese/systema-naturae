import type { BookNode } from "../types";

const IUCN_LABELS: Record<string, string> = {
  EX: "Extinct",
  EW: "Extinct in the Wild",
  CR: "Critically Endangered",
  EN: "Endangered",
  VU: "Vulnerable",
  NT: "Near Threatened",
  LC: "Least Concern",
  DD: "Data Deficient",
  NE: "Not Evaluated",
};

// Standard IUCN Red List category colors.
const IUCN_COLORS: Record<string, string> = {
  EX: "#1a1a1a",
  EW: "#4b2e57",
  CR: "#d21f1f",
  EN: "#e8721a",
  VU: "#e8c11a",
  NT: "#9bc23a",
  LC: "#3a9e3a",
  DD: "#9a9a9a",
  NE: "#c4c4c4",
};

function IucnBadge({ code }: { code: string }) {
  const label = IUCN_LABELS[code];
  if (!label) return null;
  return (
    <span
      title={label}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.3rem",
        fontSize: "0.7rem",
        letterSpacing: "0.03em",
        color: "var(--ink-soft)",
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: IUCN_COLORS[code],
          display: "inline-block",
          flexShrink: 0,
        }}
      />
      {label}
    </span>
  );
}

export function SpeciesEntry({ species }: { species: BookNode }) {
  const hasContent = Boolean(species.description || species.namedAfter || species.continents?.length);
  const dagger = species.extinct || species.fossil ? "† " : "";

  return (
    <div
      style={{
        display: "flex",
        gap: "1rem",
        padding: "0.85rem 0",
        borderBottom: "1px solid var(--paper-shadow)",
      }}
    >
      {species.imageUrl && (
        <img
          src={species.imageUrl}
          alt={species.commonName || species.name}
          loading="lazy"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
          style={{
            width: 96,
            height: 96,
            // "contain" (not "cover") so elongated animals - sharks, snakes,
            // eels - never lose their head/tail to a center-crop; the
            // tradeoff is letterboxing on non-square photos, which the
            // paper-colored background below makes read as a deliberate
            // plate border rather than an artifact.
            objectFit: "contain",
            background: "var(--paper-shadow)",
            borderRadius: "3px",
            border: "1px solid var(--paper-shadow)",
            boxShadow: "0 2px 6px rgba(42,33,24,0.15)",
            flexShrink: 0,
          }}
        />
      )}

      <div style={{ flex: 1, minWidth: 0 }}>
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
          {species.iucnStatus && <IucnBadge code={species.iucnStatus} />}
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
    </div>
  );
}
