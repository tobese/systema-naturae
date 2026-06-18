import { useState, useCallback, useMemo } from "react";
import rawNews from "../../data/species-news.json";

const LS_KEY = "species-news-seen-at";

export interface NewsEvent {
  id: string;
  date: string;
  type: "new_species" | "extinction" | "family_added";
  name: string;
  commonName: string;
  familySlug: string;
  source: "GBIF" | "IUCN" | "portal";
  url?: string;
}

interface UseSpeciesNewsResult {
  events: NewsEvent[];
  unreadCount: number;
  markAllSeen: () => void;
}

export function useSpeciesNews(): UseSpeciesNewsResult {
  const [seenAt, setSeenAt] = useState<string>(
    () => localStorage.getItem(LS_KEY) ?? "1970-01-01",
  );

  const events = useMemo(
    () => (rawNews as { updatedAt: string; events: NewsEvent[] }).events,
    [],
  );

  const unreadCount = useMemo(
    () => events.filter(e => e.date > seenAt).length,
    [events, seenAt],
  );

  const markAllSeen = useCallback(() => {
    const today = new Date().toISOString().split("T")[0];
    localStorage.setItem(LS_KEY, today);
    setSeenAt(today);
  }, []);

  return { events, unreadCount, markAllSeen };
}
