import { createContext } from "react";

export interface BookOptions {
  showExtinct: boolean;
  toggleShowExtinct: () => void;
}

export const BookOptionsContext = createContext<BookOptions | null>(null);
