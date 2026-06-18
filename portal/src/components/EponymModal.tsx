import { useEffect, useMemo, useState } from "react";
import type { TaxonNode } from "@shared/types";

interface Props {
  data: TaxonNode;
  onClose: () => void;
  onNavigate: (familySlug: string | null, nodeId: string) => void;
}

interface EponymSpecies {
  id: string;
  name: string;
  commonName?: string;
  familySlug?: string;
}

interface Honoree {
  person: string;
  species: EponymSpecies[];
}

function buildHonorees(root: TaxonNode): Honoree[] {
  const map = new Map<string, EponymSpecies[]>();

  function walk(node: TaxonNode) {
    if (node.namedAfter) {
      const entry: EponymSpecies = {
        id: node.id,
        name: node.name,
        commonName: node.commonName,
        familySlug: node.familySlug,
      };
      const list = map.get(node.namedAfter);
      if (list) list.push(entry);
      else map.set(node.namedAfter, [entry]);
    }
    node.children?.forEach(walk);
  }

  walk(root);

  return Array.from(map.entries())
    .map(([person, species]) => ({ person, species }))
    .sort((a, b) => a.person.localeCompare(b.person));
}

// Module-level cache — survives modal open/close
const checkedNames = new Set<string>();
const confirmedLinks = new Map<string, string>(); // person name → Wikipedia URL

async function resolveWikiLinks(names: string[]): Promise<void> {
  const toCheck = names.filter(n => !checkedNames.has(n));
  if (toCheck.length === 0) return;

  for (let i = 0; i < toCheck.length; i += 50) {
    const batch = toCheck.slice(i, i + 50);

    // Map URL slug → original person name
    const slugToName = new Map<string, string>();
    for (const name of batch) {
      slugToName.set(name.replace(/ /g, "_"), name);
    }

    const titlesParam = [...slugToName.keys()].join("|");
    try {
      const resp = await fetch(
        `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(titlesParam)}&format=json&origin=*&redirects=1`
      );
      const json = await resp.json();

      // Track title → original name through normalization and redirects
      const titleToName = new Map<string, string>(slugToName);
      for (const norm of json.query?.normalized ?? []) {
        const orig = slugToName.get(norm.from);
        if (orig) titleToName.set(norm.to, orig);
      }
      for (const redir of json.query?.redirects ?? []) {
        const orig = titleToName.get(redir.from);
        if (orig) titleToName.set(redir.to, orig);
      }

      for (const page of Object.values<Record<string, unknown>>(json.query?.pages ?? {})) {
        if (!page.missing) {
          const title = page.title as string;
          const orig = titleToName.get(title);
          if (orig) {
            confirmedLinks.set(orig, `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, "_"))}`);
          }
        }
      }

      batch.forEach(n => checkedNames.add(n));
    } catch {
      batch.forEach(n => checkedNames.add(n));
    }
  }
}

export default function EponymModal({ data, onClose, onNavigate }: Props) {
  const [query, setQuery] = useState("");
  const [wikiLinks, setWikiLinks] = useState<Map<string, string>>(new Map(confirmedLinks));

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { e.stopPropagation(); onClose(); }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const honorees = useMemo(() => buildHonorees(data), [data]);

  useEffect(() => {
    const names = honorees.map(h => h.person);
    resolveWikiLinks(names).then(() => setWikiLinks(new Map(confirmedLinks)));
  }, [honorees]);

  const filtered = useMemo(() => {
    if (!query.trim()) return honorees;
    const q = query.toLowerCase();
    return honorees.filter(h => h.person.toLowerCase().includes(q));
  }, [honorees, query]);

  const isFiltering = query.trim().length > 0;

  const withLetterDividers = useMemo(() => {
    if (isFiltering) return filtered.map((h, i) => ({ type: "honoree" as const, honoree: h, key: `h-${i}` }));
    const result: Array<{ type: "letter"; letter: string; key: string } | { type: "honoree"; honoree: Honoree; key: string }> = [];
    let lastLetter = "";
    let li = 0;
    for (let i = 0; i < filtered.length; i++) {
      const h = filtered[i];
      const letter = h.person[0].normalize("NFD")[0].toUpperCase();
      if (letter !== lastLetter) {
        result.push({ type: "letter", letter: h.person[0].toUpperCase(), key: `letter-${li++}` });
        lastLetter = letter;
      }
      result.push({ type: "honoree", honoree: h, key: `h-${i}` });
    }
    return result;
  }, [filtered, isFiltering]);

  const totalSpecies = useMemo(() => honorees.reduce((s, h) => s + h.species.length, 0), [honorees]);

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
          maxWidth: 700,
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          position: "relative",
        }}
      >
        {/* Fixed header */}
        <div style={{ padding: "28px 32px 0", flexShrink: 0 }}>
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

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, color: "#6666aa", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 8 }}>
              Systema Naturae
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, color: "#e0e0e0", marginBottom: 6 }}>
              Eponyms
            </div>
            <div style={{ fontSize: 13, color: "#555" }}>
              {totalSpecies} species named after {honorees.length} people
            </div>
          </div>

          <input
            type="text"
            placeholder="Filter by name…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoFocus
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: "#080c12",
              border: "1px solid #1e2030",
              borderRadius: 6,
              color: "#c0c0d8",
              fontSize: 13,
              padding: "7px 12px",
              outline: "none",
              marginBottom: 16,
            }}
            onFocus={e => (e.currentTarget.style.borderColor = "#2a2d40")}
            onBlur={e => (e.currentTarget.style.borderColor = "#1e2030")}
          />

          <div style={{ borderTop: "1px solid #1e2030" }} />
        </div>

        {/* Scrollable body */}
        <div style={{ overflowY: "auto", padding: "8px 32px 28px", flex: 1 }}>
          {filtered.length === 0 && (
            <div style={{ fontSize: 13, color: "#444", padding: "20px 0" }}>No results</div>
          )}
          {withLetterDividers.map((item) => {
            if (item.type === "letter") {
              return (
                <div key={item.key} style={{
                  fontSize: 10,
                  color: "#333",
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  padding: "14px 0 6px",
                  borderBottom: "1px solid #111620",
                  marginBottom: 4,
                }}>
                  {item.letter}
                </div>
              );
            }

            const { honoree } = item;
            const wikiUrl = wikiLinks.get(honoree.person);
            return (
              <div
                key={item.key}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 16,
                  padding: "6px 0",
                  borderBottom: "1px solid #0d1018",
                }}
              >
                <div style={{
                  width: 200,
                  flexShrink: 0,
                  fontSize: 13,
                  paddingTop: 3,
                  lineHeight: 1.4,
                }}>
                  {wikiUrl ? (
                    <a
                      href={wikiUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: "#9aaacc",
                        textDecoration: "none",
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.color = "#c0ccee";
                        e.currentTarget.style.textDecoration = "underline";
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.color = "#9aaacc";
                        e.currentTarget.style.textDecoration = "none";
                      }}
                    >
                      {honoree.person}
                    </a>
                  ) : (
                    <span style={{ color: "#c0c0d8" }}>{honoree.person}</span>
                  )}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4, flex: 1 }}>
                  {honoree.species.map(sp => (
                    <button
                      key={sp.id}
                      onClick={() => { onNavigate(sp.familySlug ?? null, sp.id); onClose(); }}
                      title={sp.name}
                      style={{
                        background: "#0d1118",
                        border: "1px solid #1e2838",
                        borderRadius: 4,
                        fontSize: 11,
                        color: "#8899aa",
                        padding: "3px 8px",
                        cursor: "pointer",
                        fontFamily: "inherit",
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.borderColor = "#2a3a4a";
                        e.currentTarget.style.color = "#aabbcc";
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.borderColor = "#1e2838";
                        e.currentTarget.style.color = "#8899aa";
                      }}
                    >
                      {sp.commonName ?? sp.name}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
