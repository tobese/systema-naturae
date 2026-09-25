import { useState, type ReactNode } from "react";
import { BookOptionsContext } from "./bookOptionsContext";

function readStored(key: string): boolean {
  try {
    return localStorage.getItem(key) === "true";
  } catch {
    return false;
  }
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

export function BookOptionsProvider({ children }: { children: ReactNode }) {
  const [showExtinct, toggleShowExtinct] = usePersistedToggle("book-view:show-extinct");
  const [showStubs, toggleShowStubs] = usePersistedToggle("book-view:show-stubs");
  const [showEmptyFamilies, toggleShowEmptyFamilies] = usePersistedToggle("book-view:show-empty-families");

  return (
    <BookOptionsContext.Provider
      value={{
        showExtinct,
        toggleShowExtinct,
        showStubs,
        toggleShowStubs,
        showEmptyFamilies,
        toggleShowEmptyFamilies,
      }}
    >
      {children}
    </BookOptionsContext.Provider>
  );
}
