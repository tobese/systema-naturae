import { useEffect, useState } from "react";
import type { BookNode } from "../types";
import { synonymTarget } from "../lib/synonyms";

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

const WIKI_BASE = "https://en.wikipedia.org/wiki/";

// A binomial's article slug is the name with spaces replaced by underscores
// (en.wikipedia also accepts the space-URL directly; underscores keep the
// href canonical). Both the entry's own name and the picked-up accepted name
// get linked - dotted underline reads as a footnote/reference in the book.
function wikiSlug(name: string): string {
  return `${WIKI_BASE}${name.replace(/ /g, "_")}`;
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
      syn. of{" "}
      <a
        href={wikiSlug(of)}
        target="_blank"
        rel="noreferrer"
        title={`Open ${of} on Wikipedia`}
        style={{
          marginLeft: "0.25em",
          color: "inherit",
          textDecoration: "none",
          borderBottom: "1px dotted currentColor",
        }}
      >
        <em>{of}</em>
      </a>
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
  const isBreed = species.rank === "BREED";
  // `lineage` is populated on almost every species (genus/group label used
  // for tree coloring elsewhere in the portal) - only meaningful as reading
  // content here for HYBRID nodes, where it's parentage text ("A ♂ × B ♀").
  const isHybrid = species.rank === "HYBRID";
  const hasContent = Boolean(
    species.description ||
      species.namedAfter ||
      species.continents?.length ||
      (isHybrid && species.lineage) ||
      (isBreed && (species.origin || species.coatType)) ||
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
              // eels - never lose their head/tail to a center-crop. Nothing is
              // drawn around the picture: no border, no backing plate - the
              // photos simply sit on the page.
              objectFit: "contain",
              borderRadius: "3px",
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
                borderRadius: 6,
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
          <span style={{ fontFamily: "var(--font-display)", fontStyle: isBreed ? "normal" : "italic", fontSize: "1.05rem" }}>
            {dagger}
            {synonym ? (
              <a
                href={wikiSlug(species.name)}
                target="_blank"
                rel="noreferrer"
                title={`Open ${species.name} on Wikipedia`}
                style={{
                  color: "inherit",
                  textDecoration: "none",
                  borderBottom: "1px dotted currentColor",
                }}
              >
                {species.name}
              </a>
            ) : (
              species.name
            )}
          </span>
          {species.commonName && (
            <span style={{ fontSize: "0.9rem", color: "var(--ink-soft)" }}>{species.commonName}</span>
          )}
          {isBreed && species.origin && (
            <span style={{ fontSize: "0.85rem", color: "var(--ink-soft)" }}>from {species.origin}</span>
          )}
          {isBreed && species.coatType && (
            <span style={{ fontSize: "0.8rem", fontStyle: "italic", color: "var(--ink-faint)" }}>
              {species.coatType}
            </span>
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
          <div style={{ marginTop: "0.6rem" }}>
            {groups.map((group) => (
              <div key={group.id} style={{ marginTop: "0.6rem" }}>
                <div
                  style={{
                    fontSize: "0.8rem",
                    letterSpacing: "0.04em",
                    textTransform: "uppercase",
                    color: "var(--ink-faint)",
                    borderBottom: "1px solid var(--paper-shadow)",
                    paddingBottom: "0.15rem",
                    marginBottom: "0.1rem",
                  }}
                >
                  {group.name}
                </div>
                {(group.children ?? []).map((breed) => (
                  <SpeciesEntry key={breed.id} species={breed} />
                ))}
              </div>
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
