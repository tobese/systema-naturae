import { useContext } from "react";
import { BookOptionsContext, type BookOptions } from "../context/bookOptionsContext";

export function useBookOptions(): BookOptions {
  const ctx = useContext(BookOptionsContext);
  if (!ctx) throw new Error("useBookOptions must be used within a BookOptionsProvider");
  return ctx;
}
