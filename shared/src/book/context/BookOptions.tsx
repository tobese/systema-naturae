import { useState, type ReactNode } from "react";
import { BookOptionsContext } from "./bookOptionsContext";
import { DEFAULT_MIN_DESCRIPTION_LENGTH } from "../../lib/description";

function readStored(key: string): boolean {
  try {
    return localStorage.getItem(key) === "true";
  } catch {
    return false;
  }
}

function usePersistedNumber(key: string, fallback: number): [number, (n: number) => void] {
  const [value, setValue] = useState(() => {
    try {
      const raw = localStorage.getItem(key);
      const n = raw === null ? NaN : parseInt(raw, 10);
      return Number.isFinite(n) ? n : fallback;
    } catch {
      return fallback;
    }
  });
  const set = (n: number) => {
    setValue(n);
    try {
      localStorage.setItem(key, String(n));
    } catch {
      /* not persisted; option still applies for this session */
    }
  };
  return [value, set];
}

function usePersistedToggle(key: string): [boolean, () => void] {
  const [value, setValue] = useState(() => readStored(key));
  const toggle = () => {
    setValue((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(key, String(next));
      } catch {
        // localStorage unavailable (private browsing, etc.) - option just won't persist
      }
      return next;
    });
  };
  return [value, toggle];
}

export function BookOptionsProvider({
  children,
  hideThinDescriptions: hideOverride,
  minDescriptionLength: minOverride,
}: {
  children: ReactNode;
  /**
   * Optional host control of the description gate.
   *
   * The portal has no book-specific options UI - showStubs and
   * showEmptyFamilies are readable and persisted but nothing in the portal
   * toggles them, they exist for the standalone book app. So rather than add a
   * second toggle that nobody can reach, the portal's one ⚙ switch passes its
   * values in here and both surfaces follow it.
   *
   * When an override is supplied it wins and localStorage is not consulted, so
   * there is exactly one source of truth per surface. With no override - the
   * standalone app - the persisted local toggles apply as before.
   */
  hideThinDescriptions?: boolean;
  minDescriptionLength?: number;
}) {
  const [showExtinct, toggleShowExtinct] = usePersistedToggle("book-view:show-extinct");
  const [showStubs, toggleShowStubs] = usePersistedToggle("book-view:show-stubs");
  const [showEmptyFamilies, toggleShowEmptyFamilies] = usePersistedToggle("book-view:show-empty-families");
  const [persistedHide, togglePersistedHide] = usePersistedToggle("book-view:hide-thin-descriptions");
  const [persistedMin, setPersistedMin] = usePersistedNumber(
    "book-view:min-description-length", DEFAULT_MIN_DESCRIPTION_LENGTH);

  const hideThinDescriptions = hideOverride ?? persistedHide;
  const minDescriptionLength = minOverride ?? persistedMin;
  const toggleHideThinDescriptions = hideOverride === undefined ? togglePersistedHide : () => {};
  const setMinDescriptionLength =
    minOverride === undefined ? setPersistedMin : (_n: number) => {};

  return (
    <BookOptionsContext.Provider
      value={{
        showExtinct,
        toggleShowExtinct,
        showStubs,
        toggleShowStubs,
        showEmptyFamilies,
        hideThinDescriptions,
        toggleHideThinDescriptions,
        minDescriptionLength,
        setMinDescriptionLength,
        toggleShowEmptyFamilies,
      }}
    >
      {children}
    </BookOptionsContext.Provider>
  );
}
