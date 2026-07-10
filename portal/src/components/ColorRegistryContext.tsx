import { createContext, useContext } from "react";
import type { ColorTheme } from "@shared/types";

export const ColorRegistryContext = createContext<Record<string, ColorTheme>>({});

export function useColorRegistry(): Record<string, ColorTheme> {
  return useContext(ColorRegistryContext);
}
