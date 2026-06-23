import { useState, useEffect } from "react";
import ImportTimeline from "./ImportTimeline";

interface Props {
  onClose: () => void;
}

export default function InfoModal({ onClose }: Props) {
  const [tab, setTab] = useState<"about" | "growth">("about");

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const TAB = (key: string, label: string) => (
    <button
      onClick={() => setTab(key as any)}
      style={{
        background: "none",
        border: "none",
        color: tab === key ? "#c0c0d8" : "#444",
        fontSize: 11,
        cursor: "pointer",
        padding: "6px 0",
        borderBottom: tab === key ? "1px solid #6a8aba" : "1px solid transparent",
        letterSpacing: "0.06em",
        textTransform: "uppercase" as const,
      }}
    >
      {label}
    </button>
  );

  const isWide = tab === "growth";

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.72)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: "#0f1117",
          border: "1px solid #1e2030",
          borderRadius: 10,
          width: "100%",
          maxWidth: isWide ? 740 : 580,
          maxHeight: "80vh",
          overflowY: "auto",
          position: "relative",
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          title="Close"
          style={{
            position: "absolute",
            top: 12,
            right: 14,
            width: 28,
            height: 28,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "transparent",
            border: "none",
            color: "#444",
            fontSize: 18,
            cursor: "pointer",
            borderRadius: 4,
          }}
          onMouseEnter={e => (e.currentTarget.style.color = "#aaa")}
          onMouseLeave={e => (e.currentTarget.style.color = "#444")}
        >
          ×
        </button>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 20, padding: "28px 32px 0" }}>
          {TAB("about", "About")}
          {TAB("growth", "Growth")}
        </div>

        {/* Content */}
        {tab === "about" && (
          <div style={{ padding: "28px 32px 32px" }}>
            <div style={{ display: "flex", gap: 24, alignItems: "flex-start", marginBottom: 24 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
                  Systema Naturae · 1735
                </div>
                <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 10, lineHeight: 1.2 }}>
                  Carl Linnaeus
                </div>
                <table style={{ borderCollapse: "collapse", fontSize: 11 }}>
                  <tbody>
                    {[
                      ["Born", "23 May 1707 · Råshult, Sweden"],
                      ["Died", "10 Jan 1778 · Uppsala, Sweden"],
                      ["Field", "Botany · Zoology · Taxonomy"],
                      ["Known for", "Systema Naturae · Binomial nomenclature"],
                    ].map(([label, value]) => (
                      <tr key={label}>
                        <td style={{ color: "#444", paddingRight: 12, paddingBottom: 4, whiteSpace: "nowrap", verticalAlign: "top" }}>{label}</td>
                        <td style={{ color: "#888", paddingBottom: 4 }}>{value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={{ flexShrink: 0 }}>
                <img
                  src="/linnaeus.jpg"
                  alt="Carl Linnaeus, portrait by Alexander Roslin, 1775"
                  width={110}
                  style={{ display: "block", borderRadius: 4, border: "1px solid #1e2030", filter: "brightness(0.88) contrast(1.05)" }}
                />
                <div style={{ fontSize: 9, color: "#333", marginTop: 4, textAlign: "center" }}>A. Roslin, 1775</div>
              </div>
            </div>

            <div style={{ borderTop: "1px solid #1e2030", marginBottom: 22 }} />

            <div style={{ fontSize: 14, color: "#999", lineHeight: 1.7, display: "flex", flexDirection: "column", gap: 16 }}>
              <p style={{ margin: 0 }}>
                Before Linnaeus, plants and animals carried long, unwieldy Latin descriptions that differed from author to author. There was no shared language for life. He became the first person to impose systematic order on the natural world.
              </p>
              <p style={{ margin: 0 }}>
                In 1735, aged 28, he published the first edition of <em style={{ color: "#c0c0d8" }}>Systema Naturae</em> — eleven folio pages arranging the three kingdoms of nature (animals, plants, minerals) into a nested hierarchy of classes, orders, genera, and species. The idea that all living things could be sorted into ranks, and that each species could be pinned to a two-part Latin name shared by everyone, was radical. It worked.
              </p>
              <p style={{ margin: 0 }}>
                By the 12th edition in 1768, the book had grown to 2,400 pages, naming some 7,700 plants and 6,200 animals. Every species in this portal traces its scientific name to the system Linnaeus built — the <em style={{ color: "#c0c0d8" }}>binomial nomenclature</em> that pairs a genus with a species epithet: <em style={{ color: "#c0c0d8" }}>Panthera leo</em>, <em style={{ color: "#c0c0d8" }}>Homo sapiens</em>, <em style={{ color: "#c0c0d8" }}>Milnesium tardigradum</em>.
              </p>
              <p style={{ margin: 0 }}>
                This portal borrows his title and his structure. The same ranked hierarchy — kingdom, phylum, class, order, family, genus, species — organises everything here. The ambition is the same too: a single place where the diversity of animal life can be held, browsed, and understood.
              </p>
            </div>

            <div style={{ borderTop: "1px solid #1e2030", margin: "24px 0 20px" }} />

            <p style={{ margin: 0, fontSize: 13, color: "#6666aa", fontStyle: "italic", lineHeight: 1.6 }}>
              "Natura non facit saltus."<br />
              <span style={{ fontSize: 11, color: "#444" }}>Nature makes no leaps. — Linnaeus, <em>Philosophia Botanica</em>, 1751</span>
            </p>
          </div>
        )}

        {tab === "growth" && (
          <div style={{ padding: "20px 32px 32px" }}>
            <ImportTimeline />
          </div>
        )}
      </div>
    </div>
  );
}
