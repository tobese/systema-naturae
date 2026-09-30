import { createContext, useContext, type ReactNode } from "react";
import { DEFAULT_MIN_DESCRIPTION_LENGTH, showDescription } from "@shared/lib/description";

/**
 * Display gate for stored descriptions.
 *
 * A context rather than props because UnifiedInfoPanel dispatches to ten
 * per-rank sub-panels (KingdomPanel, PhylumPanel, … SpeciesPanel) and each one
 * renders its own description. Threading two props through ten components to
 * reach one conditional in each is the wrong shape for what is, in the end, one
 * user preference.
 *
 * Defaults are the *permissive* ones: gate off, length at the import default.
 * So a component rendered outside a provider behaves exactly as it did before
 * this existed, and forgetting to wrap something degrades to "no change"
 * rather than to "hides everything".
 */
const DescriptionGateContext = createContext<{ show: (text: string | undefined | null) => string }>({
  show: text => (text ?? "").trim(),
});

export function DescriptionGateProvider({
  hideThinDescriptions,
  minDescriptionLength = DEFAULT_MIN_DESCRIPTION_LENGTH,
  children,
}: {
  hideThinDescriptions: boolean;
  minDescriptionLength?: number;
  children: ReactNode;
}) {
  const min = hideThinDescriptions ? minDescriptionLength : 0;   // 0 = show all
  return (
    <DescriptionGateContext.Provider value={{ show: text => showDescription(text, min) }}>
      {children}
    </DescriptionGateContext.Provider>
  );
}

/** The text to render, or "" when the gate hides it. */
export function useDescriptionGate(): { show: (text: string | undefined | null) => string } {
  return useContext(DescriptionGateContext);
}
