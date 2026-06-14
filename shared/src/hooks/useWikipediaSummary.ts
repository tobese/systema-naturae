import { useState, useEffect } from "react";

interface WikiSummary {
  extract: string;
  thumbnail?: { source: string };
  content_urls?: { desktop: { page: string } };
}

export function useWikipediaSummary(title: string | null) {
  const [data, setData] = useState<WikiSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!title) { setData(null); return; }
    setLoading(true);
    fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/ /g, "_"))}`
    )
      .then(r => (r.ok ? r.json() : null))
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setData(null); setLoading(false); });
  }, [title]);

  return { data, loading };
}
