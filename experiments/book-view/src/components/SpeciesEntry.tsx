import { useEffect, useState } from "react";
import type { BookNode } from "../types";

// Commons' Special:FilePath endpoint (see extractSlice.ts's commonsThumb)
// renders whatever width is requested, capped at the source resolution - so
// a bigger picture is just a bigger `width` query param, no re-extraction
// needed.
function withWidth(url: string, width: number): string {
  return url.replace(/([?&])width=\d+/, `$1width=${width}`);
}

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

// Some species in the tree carry an old/regional scientific name whose
// Wikipedia-sourced description was written for the currently-accepted name
// instead (no separate article exists for the synonym) - e.g. Felidae's
// "Felis lanea" (a real 1877 synonym per GBIF/Wilson & Reeder) describing
// "the cheetah (Acinonyx jubatus)". Detected here rather than at extract
// time since it only needs the description text already on the node.
// Restricted to the first 60 characters so a binomial mentioned deeper in
// the prose (a related species, say) isn't mistaken for the entry's own
// accepted name; excludes apostrophes so a restated common name in
// parens - "Lontra weiri (Weir's otter)" - doesn't parse as a fake genus.
const SYNONYM_RE = /^.{0,60}\(([A-Z][a-zà-ÿ-]+)\s+([a-zà-ÿ×-]+)\)/;

function synonymTarget(species: BookNode): string | null {
  if (!species.description) return null;
  const m = SYNONYM_RE.exec(species.description);
  if (!m) return null;
  const [, genus, epithet] = m;
  const ownGenus = species.name.split(" ")[0];
  if (genus.toLowerCase() === ownGenus.toLowerCase()) return null;
  return `${genus} ${epithet}`;
}

function SynonymTag({ of }: { of: string }) {
  return (
    <span
      title={`This name is a synonym; the description above is sourced from ${of}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontSize: "0.7rem",
        letterSpacing: "0.03em",
        color: "var(--ink-faint)",
        border: "1px solid var(--paper-shadow)",
        borderRadius: "2px",
        padding: "0.05rem 0.4rem",
      }}
    >
      syn. of <em style={{ marginLeft: "0.25em" }}>{of}</em>
    </span>
  );
}

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

// Full-screen lightbox for the clicked-open picture. Escape and a click
// anywhere (backdrop or image) both close it - there's no separate close
// button, matching how the hover preview needs no dismiss affordance either.
function Lightbox({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15,10,8,0.88)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        cursor: "zoom-out",
        padding: "2rem",
      }}
    >
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: "90vw",
          maxHeight: "85vh",
          objectFit: "contain",
          borderRadius: 4,
          boxShadow: "0 12px 48px rgba(0,0,0,0.6)",
        }}
      />
    </div>
  );
}

// Only SPECIES nodes with domesticated breeds (Equidae, Canidae-style
// pedigree families) nest a nested BREED_GROUP > BREED layer under
// `children`; SUBSPECIES nests there too (already summarized via
// `subspeciesCount`, not listed out), so only render for the breed case.
function breedGroups(species: BookNode): BookNode[] {
  const children = species.children ?? [];
  return children[0]?.rank === "BREED_GROUP" ? children : [];
}

export function SpeciesEntry({ species }: { species: BookNode }) {
  const groups = breedGroups(species);
  // `lineage` is populated on almost every species (genus/group label used
  // for tree coloring elsewhere in the portal) - only meaningful as reading
  // content here for HYBRID nodes, where it's parentage text ("A ♂ × B ♀").
  const isHybrid = species.rank === "HYBRID";
  const hasContent = Boolean(
    species.description ||
      species.namedAfter ||
      species.continents?.length ||
      (isHybrid && species.lineage) ||
      groups.length,
  );
  const dagger = species.extinct || species.fossil ? "† " : "";
  const synonym = synonymTarget(species);
  const [hovering, setHovering] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);

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
        <div
          style={{ position: "relative", flexShrink: 0 }}
          onMouseEnter={() => setHovering(true)}
          onMouseLeave={() => setHovering(false)}
        >
          <img
            src={species.imageUrl}
            alt={species.commonName || species.name}
            loading="lazy"
            onClick={() => setLightboxOpen(true)}
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
              cursor: "zoom-in",
            }}
          />
          {hovering && (
            <img
              src={withWidth(species.imageUrl, 400)}
              alt=""
              aria-hidden="true"
              style={{
                position: "absolute",
                top: 0,
                left: "110%",
                width: 260,
                height: 260,
                objectFit: "contain",
                background: "var(--paper)",
                borderRadius: 4,
                border: "1px solid var(--paper-shadow)",
                boxShadow: "0 8px 28px rgba(0,0,0,0.35)",
                zIndex: 20,
                pointerEvents: "none",
              }}
            />
          )}
          {lightboxOpen && (
            <Lightbox
              src={withWidth(species.imageUrl, 1600)}
              alt={species.commonName || species.name}
              onClose={() => setLightboxOpen(false)}
            />
          )}
        </div>
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
          {synonym && <SynonymTag of={synonym} />}
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

        {isHybrid && species.lineage && (
          <p style={{ margin: "0.3rem 0 0", fontSize: "0.85rem", fontStyle: "italic", color: "var(--ink-faint)" }}>
            {species.lineage}
          </p>
        )}

        {groups.length > 0 && (
          <div style={{ marginTop: "0.4rem" }}>
            {groups.map((group) => (
              <p key={group.id} style={{ margin: "0.15rem 0", fontSize: "0.8rem", color: "var(--ink-faint)", lineHeight: 1.6 }}>
                <span style={{ fontStyle: "italic", color: "var(--ink-soft)" }}>{group.name}:</span>{" "}
                {(group.children ?? []).map((b) => (b.origin ? `${b.name} (${b.origin})` : b.name)).join(", ")}
              </p>
            ))}
          </div>
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
