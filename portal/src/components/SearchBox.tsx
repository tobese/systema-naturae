import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import type { TaxonNode } from "@shared/types";

interface SearchEntry {
  id: string;
  name: string;
  commonName?: string;
  rank: string;
  familySlug?: string;
}

const SKIP_RANKS = new Set(["KINGDOM", "PHYLUM"]);

function buildIndex(node: TaxonNode, entries: SearchEntry[] = []): SearchEntry[] {
  if (!SKIP_RANKS.has(node.rank)) {
    entries.push({ id: node.id, name: node.name, commonName: node.commonName, rank: node.rank, familySlug: node.familySlug });
  }
  for (const child of node.children ?? []) buildIndex(child, entries);
  return entries;
}

function scoreMatch(entry: SearchEntry, q: string): number {
  const lower = q.toLowerCase();
  const nameMatch = entry.name.toLowerCase().startsWith(lower) ? 2 : entry.name.toLowerCase().includes(lower) ? 1 : 0;
  const commonMatch = entry.commonName
    ? entry.commonName.toLowerCase().startsWith(lower) ? 2 : entry.commonName.toLowerCase().includes(lower) ? 1 : 0
    : 0;
  return Math.max(nameMatch, commonMatch);
}

const RANK_LABELS: Record<string, string> = {
  CLASS: "Class", ORDER: "Order", FAMILY: "Family", SUBFAMILY: "Subfamily",
  TRIBE: "Tribe", GENUS: "Genus", SPECIES: "Species", SUBSPECIES: "Subspecies",
  BREED_GROUP: "Breed Group", BREED: "Breed", HYBRID_GROUP: "Hybrid Group", HYBRID: "Hybrid",
};

interface Props {
  data: TaxonNode;
  onNavigate: (family: string | null, nodeId: string | null) => void;
}

export default function SearchBox({ data, onNavigate }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const index = useMemo(() => buildIndex(data), [data]);

  const results = useMemo(() => {
    if (query.trim().length < 2) return [];
    const q = query.trim();
    return index
      .map(e => ({ entry: e, score: scoreMatch(e, q) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
      .map(x => x.entry);
  }, [index, query]);

  useEffect(() => { setActiveIndex(0); }, [results]);

  const select = useCallback((entry: SearchEntry) => {
    if (entry.rank === "FAMILY") {
      onNavigate(entry.familySlug ?? null, null);
    } else if (entry.familySlug) {
      onNavigate(entry.familySlug, entry.id);
    } else {
      onNavigate(null, entry.id);
    }
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  }, [onNavigate]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIndex(i => (i + 1) % results.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIndex(i => (i - 1 + results.length) % results.length); }
    else if (e.key === "Enter") { e.preventDefault(); select(results[activeIndex]); }
    else if (e.key === "Escape") { setOpen(false); inputRef.current?.blur(); }
  }, [open, results, activeIndex, select]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const showDropdown = open && results.length > 0;

  return (
    <div ref={containerRef} style={{ position: "relative", flex: 1, maxWidth: 300, margin: "0 16px" }}>
      <input
        ref={inputRef}
        value={query}
        onChange={e => { setQuery(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder="Search…"
        style={{
          width: "100%",
          padding: "6px 12px",
          borderRadius: 6,
          border: "1px solid #1e2030",
          background: "#141420",
          color: "#e0e0e0",
          fontSize: 13,
          outline: "none",
          boxSizing: "border-box",
        }}
      />
      {showDropdown && (
        <div style={{
          position: "absolute",
          top: "calc(100% + 4px)",
          left: 0,
          right: 0,
          background: "#141420",
          border: "1px solid #1e2030",
          borderRadius: 6,
          overflow: "hidden",
          zIndex: 100,
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        }}>
          {results.map((entry, i) => {
            const primary = entry.commonName ?? entry.name;
            const secondary = entry.commonName ? entry.name : null;
            const rankLabel = RANK_LABELS[entry.rank] ?? entry.rank;
            return (
              <div
                key={entry.id}
                onMouseDown={e => { e.preventDefault(); select(entry); }}
                onMouseEnter={() => setActiveIndex(i)}
                style={{
                  padding: "7px 12px",
                  cursor: "pointer",
                  background: i === activeIndex ? "#1e2030" : "transparent",
                  borderBottom: i < results.length - 1 ? "1px solid #1a1a2a" : undefined,
                }}
              >
                <div style={{ fontSize: 13, color: "#e0e0e0", fontWeight: 500 }}>{primary}</div>
                <div style={{ fontSize: 11, color: "#556", marginTop: 1 }}>
                  {secondary && <span style={{ fontStyle: "italic", marginRight: 6 }}>{secondary}</span>}
                  <span style={{
                    background: "#1e2030",
                    borderRadius: 3,
                    padding: "1px 4px",
                    fontSize: 10,
                    color: "#8899cc",
                    marginRight: 4,
                  }}>{rankLabel}</span>
                  {entry.familySlug && <span style={{ color: "#445" }}>{entry.familySlug}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
