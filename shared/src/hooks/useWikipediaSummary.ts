import { useState, useEffect } from "react";
import { fetchWikiSummary, type WikiSummary } from "../lib/wikiSummary";

// Resolves through shared/src/lib/wikiSummary.ts, which picks the self-hosted
// mirror (VITE_WIKI_SUMMARY_BASE, development) or the public REST API
// (deployed builds). The summary type is re-exported so existing consumers that
// import it from here keep working.
export type { WikiSummary };

export function useWikipediaSummary(title: string | null) {
  const [data, setData] = useState<WikiSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!title) { setData(null); return; }
    let cancelled = false;
    setLoading(true);
    fetchWikiSummary(title)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [title]);

  return { data, loading };
}
