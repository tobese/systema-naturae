import { useState } from "react";

// The single skeuomorphic beat in the app: a book cover you click to open.
// Everything past this point is a refined but flat "book-styled" reading view,
// not literal page-turning — see plan §4 for why.
export function CoverSplash({ onOpen }: { onOpen: () => void }) {
  const [opening, setOpening] = useState(false);

  const handleOpen = () => {
    setOpening(true);
    window.setTimeout(onOpen, 700);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleOpen}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && handleOpen()}
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        background: "var(--cover-bg)",
        perspective: "2400px",
      }}
    >
      <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.06" />
          </feComponentTransfer>
          <feComposite operator="over" in2="SourceGraphic" />
        </filter>
      </svg>
      <div
        style={{
          width: "min(72vw, 460px)",
          aspectRatio: "2 / 3",
          borderRadius: "2px",
          background:
            "linear-gradient(155deg, #5a1e28 0%, #3c141b 55%, #260c11 100%)",
          boxShadow:
            "0 30px 70px rgba(0,0,0,0.6), inset 0 0 0 2px rgba(212,175,110,0.35), inset 0 0 40px rgba(0,0,0,0.5)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "1.5rem",
          padding: "3rem 2rem",
          transformOrigin: "left center",
          transform: opening ? "rotateY(-25deg) translateX(-6%)" : "rotateY(0deg)",
          opacity: opening ? 0 : 1,
          transition: "transform 0.7s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.7s ease-out 0.15s",
          filter: "url(#grain)",
        }}
      >
        <div
          style={{
            border: "1px solid rgba(212,175,110,0.55)",
            padding: "0.4rem 0.9rem",
            fontFamily: "var(--font-display)",
            fontSize: "0.7rem",
            letterSpacing: "0.3em",
            color: "rgba(230,208,160,0.85)",
          }}
        >
          REGNUM ANIMALE
        </div>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(2.2rem, 8vw, 3.2rem)",
            letterSpacing: "0.08em",
            color: "#e8cf94",
            textAlign: "center",
            textShadow: "0 1px 0 rgba(255,235,190,0.25), 0 2px 6px rgba(0,0,0,0.6)",
            lineHeight: 1.1,
          }}
        >
          SYSTEMA
          <br />
          NATURÆ
        </h1>
        <div
          style={{
            width: "60px",
            height: "1px",
            background: "rgba(212,175,110,0.6)",
          }}
        />
        <p
          style={{
            fontFamily: "var(--font-display)",
            fontStyle: "italic",
            color: "rgba(230,208,160,0.7)",
            fontSize: "0.95rem",
            margin: 0,
          }}
        >
          a book of species, ever unfinished
        </p>
        <p
          style={{
            marginTop: "2rem",
            fontFamily: "var(--font-body)",
            fontSize: "0.85rem",
            letterSpacing: "0.15em",
            color: "rgba(230,208,160,0.55)",
            textTransform: "uppercase",
          }}
        >
          Open the Book
        </p>
      </div>
    </div>
  );
}
