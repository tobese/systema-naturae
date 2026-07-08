import { useState, useCallback, useEffect } from "react";

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

export function useSpeciesNews(kingdom = "animalia"): UseSpeciesNewsResult {
  const [events, setEvents] = useState<NewsEvent[]>([]);
  const [seenAt, setSeenAt] = useState<string>(
    () => localStorage.getItem(LS_KEY) ?? "1970-01-01",
  );

  useEffect(() => {
    const suffix = kingdom === "animalia" ? "" : `-${kingdom}`;
    fetch(`/data/species-news${suffix}.json`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: { updatedAt?: string; events?: NewsEvent[] } | NewsEvent[]) => {
        // Animal format: wrapped object; Plantae format: plain array
        const rawEvents = Array.isArray(data) ? data : (data.events ?? []);
        // Normalize plant entries (family -> familySlug, no id/source)
        const normalized = rawEvents.map((e: any, i: number) => ({
          id: e.id ?? `${e.type}-${e.family ?? e.familySlug}-${e.date}`,
          date: e.date,
          type: e.type,
          name: e.name,
          commonName: e.commonName ?? e.name,
          familySlug: e.familySlug ?? e.family ?? "",
          source: e.source ?? "portal",
          url: e.url,
        }));
        setEvents(normalized);
      })
      .catch(() => {
        setEvents([]);
      });
  }, [kingdom]);

  const unreadCount = events.filter(e => e.date > seenAt).length;

  const markAllSeen = useCallback(() => {
    const today = new Date().toISOString().split("T")[0];
    localStorage.setItem(LS_KEY, today);
    setSeenAt(today);
  }, []);

  return { events, unreadCount, markAllSeen };
}
