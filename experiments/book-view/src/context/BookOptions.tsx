import { useState, type ReactNode } from "react";
import { BookOptionsContext } from "./bookOptionsContext";

const STORAGE_KEY = "book-view:show-extinct";

function readStored(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export function BookOptionsProvider({ children }: { children: ReactNode }) {
  const [showExtinct, setShowExtinct] = useState(readStored);

  const toggleShowExtinct = () => {
    setShowExtinct((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // localStorage unavailable (private browsing, etc.) - option just won't persist
      }
      return next;
    });
  };

  return (
    <BookOptionsContext.Provider value={{ showExtinct, toggleShowExtinct }}>
      {children}
    </BookOptionsContext.Provider>
  );
}
