import { useState, useEffect, useCallback } from "react";

function parseUrl(): { family: string | null; nodeId: string | null } {
  const p = new URLSearchParams(window.location.search);
  return { family: p.get("family"), nodeId: p.get("node") };
}

function buildUrl(family: string | null, nodeId: string | null): string {
  const p = new URLSearchParams();
  if (family) p.set("family", family);
  if (nodeId) p.set("node", nodeId);
  const qs = p.toString();
  return qs ? `?${qs}` : window.location.pathname;
}

export function useUrlState(): {
  focusedFamilySlug: string | null;
  selectedNodeId: string | null;
  setFocus: (slug: string | null) => void;
  setSelectedNodeId: (id: string | null) => void;
} {
  const [state, setState] = useState(parseUrl);

  useEffect(() => {
    const handler = () => setState(parseUrl());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  const setFocus = useCallback((slug: string | null) => {
    const url = buildUrl(slug, null);
    history.pushState(null, "", url);
    setState({ family: slug, nodeId: null });
  }, []);

  const setSelectedNodeId = useCallback((id: string | null) => {
    setState(prev => {
      const url = buildUrl(prev.family, id);
      history.pushState(null, "", url);
      return { ...prev, nodeId: id };
    });
  }, []);

  return {
    focusedFamilySlug: state.family,
    selectedNodeId: state.nodeId,
    setFocus,
    setSelectedNodeId,
  };
}
