import { useEffect, useState } from "react";

/**
 * `contributors-index.json` (written by `make contributors`): maps an id
 * stamped in a node's `sourceIds` to the dataset it names, and gives that
 * dataset's title, link, licence and institution. Fetched once and shared.
 */
export interface ContributorsIndex {
  keyMap: Record<string, string>;
  datasets: Record<string, { title: string | null; url: string | null; licence: string | null; institution: string | null }>;
}

let pending: Promise<ContributorsIndex | null> | null = null;

function load(): Promise<ContributorsIndex | null> {
  pending ??= fetch(`${import.meta.env.BASE_URL ?? "/"}data/contributors-index.json`)
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null);
  return pending;
}

export function useContributorsIndex(): ContributorsIndex | null {
  const [index, setIndex] = useState<ContributorsIndex | null>(null);
  useEffect(() => {
    let live = true;
    load().then((i) => { if (live) setIndex(i); });
    return () => { live = false; };
  }, []);
  return index;
}
