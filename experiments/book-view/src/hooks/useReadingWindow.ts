import { useCallback, useEffect, useRef, useState } from "react";

// Scroll-driven "reading window": only families within WINDOW_RADIUS of the
// section currently crossing the top of the viewport stay expanded (fully
// mounted); everything else collapses to just its header. This is what
// keeps a 146-family, ~3,200-species chapter (Passeriformes) from mounting
// all of it at once - see FamilySection.tsx for where isExpanded() gates
// the actual conditional render. One shared IntersectionObserver per
// ChapterPage instance, not one per family - cheap even at hundreds of
// sentinels.
const WINDOW_RADIUS = 1;
const UNPIN_HYSTERESIS = 3;

export interface ReadingWindow {
  isExpanded: (slug: string) => boolean;
  registerSentinel: (slug: string) => (el: HTMLElement | null) => void;
  pin: (slug: string) => void;
}

export function useReadingWindow(orderedSlugs: string[]): ReadingWindow {
  const [activeIndex, setActiveIndex] = useState(0);
  const [pinned, setPinned] = useState<Set<string>>(new Set());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelIndex = useRef<Map<Element, number>>(new Map());
  const sentinelCallbacks = useRef<Map<string, (el: HTMLElement | null) => void>>(new Map());
  // Ref callbacks fire during commit, which happens *before* the effect
  // below creates the observer - elements that mount before the observer
  // exists get queued here and flushed once it does, rather than silently
  // observing nothing (the bug this replaced: the window never advanced no
  // matter how far you scrolled, because every family's sentinel had been
  // registered against a still-null observer).
  const pendingElements = useRef<Element[]>([]);
  const slugsKey = orderedSlugs.join("|");

  // No reset-on-list-change effect needed: ChapterPage (the sole caller)
  // fully unmounts on chapter navigation, so this hook's state already
  // starts fresh per chapter. The family list itself doesn't reshape
  // within a chapter either - showExtinct filtering happens inside
  // FamilySection, not in the ordered slug list this hook windows over.

  const handleIntersect = useCallback((entries: IntersectionObserverEntry[]) => {
    let best: { index: number; top: number } | null = null;
    for (const entry of entries) {
      const index = sentinelIndex.current.get(entry.target);
      if (index === undefined) continue;
      // A sentinel that has scrolled above the trigger band (top < the
      // band) or is currently inside it counts as "reached" - take the
      // furthest (highest-index) one reached, matching how a scrollspy
      // tracks "which section are we currently in."
      if (entry.isIntersecting || entry.boundingClientRect.top < 0) {
        if (!best || index > best.index) best = { index, top: entry.boundingClientRect.top };
      }
    }
    if (best) setActiveIndex(best.index);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(handleIntersect, {
      // Trigger band: top 25% of the viewport. A family "becomes active"
      // once its header crosses into that band, giving a little pre-roll
      // before it's fully in view without expanding a whole viewport ahead.
      rootMargin: "-25% 0px -75% 0px",
      threshold: 0,
    });
    observerRef.current = observer;
    for (const el of pendingElements.current) observer.observe(el);
    pendingElements.current = [];
    return () => observer.disconnect();
  }, [slugsKey, handleIntersect]);

  // Returns a *stable* callback per slug (cached, not recreated each
  // render). This matters at scale: a fresh ref callback every render would
  // make React detach+reattach it on every render of every FamilySection,
  // each reattach re-triggering IntersectionObserver.observe() (which
  // queues a fresh notification) - at 145+ families that's a render loop
  // that pegs the main thread. Caching by slug means observe() only ever
  // runs once per element, on its actual mount.
  const registerSentinel = useCallback(
    (slug: string) => {
      let cb = sentinelCallbacks.current.get(slug);
      if (!cb) {
        cb = (el: HTMLElement | null) => {
          if (!el) return;
          const index = orderedSlugs.indexOf(slug);
          sentinelIndex.current.set(el, index);
          if (observerRef.current) observerRef.current.observe(el);
          else pendingElements.current.push(el);
        };
        sentinelCallbacks.current.set(slug, cb);
      }
      return cb;
    },
    [orderedSlugs],
  );

  const pin = useCallback((slug: string) => {
    setPinned((prev) => (prev.has(slug) ? prev : new Set(prev).add(slug)));
  }, []);

  const isExpanded = useCallback(
    (slug: string) => {
      const index = orderedSlugs.indexOf(slug);
      if (index === -1) return false;
      const distance = Math.abs(index - activeIndex);
      if (distance <= WINDOW_RADIUS) return true;
      // A pin stays "sticky" beyond the normal window, but only up to a
      // point - once the user has scrolled well past it, let it collapse
      // like everything else rather than pinning forever. No effect-driven
      // cleanup needed: the pinned Set can just keep growing, since
      // distance alone determines whether an old pin still matters.
      return pinned.has(slug) && distance <= WINDOW_RADIUS + UNPIN_HYSTERESIS;
    },
    [pinned, orderedSlugs, activeIndex],
  );

  return { isExpanded, registerSentinel, pin };
}
