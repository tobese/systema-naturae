/**
 * One definition of "too thin to be worth showing as a description".
 *
 * Why this exists
 * ---------------
 * Wikipedia's long tail is mostly stub leads. The 317 reclassifications applied
 * on 2026-09-30 sit in an 80-119 character band, and that band splits on
 * content rather than length:
 *
 *   useful      "Sphaerium transversum is a species of freshwater bivalve from
 *                the family Sphaeriidae"           - carries habitat and rank
 *   boilerplate "Acronia gloriosa is a species of beetle in the family
 *                Cerambycidae"                     - restates familyName, which
 *                                                   the tree already holds
 *
 * So the import gate is `MIN_LEAD = 80` in validateNamesWithCol.py, and this is
 * the *display* gate for text that is already stored - including the pre-existing
 * thin descriptions, which the import never touched.
 *
 * Default 80 matches the import gate. Setting it higher hides more; 0 shows
 * everything, which is the escape hatch for anyone who wants the raw text.
 */
export const DEFAULT_MIN_DESCRIPTION_LENGTH = 80;

/** True when the text should be hidden under the current display gate. */
export function isThinDescription(text: string | undefined | null, min: number): boolean {
  if (min <= 0) return false;              // 0 = show everything
  const trimmed = (text ?? "").trim();
  if (trimmed.length === 0) return true;    // nothing to show either way
  return trimmed.length < min;
}

/**
 * The description to render, or "" when the gate hides it.
 *
 * Returns "" rather than undefined so call sites can swap a conditional from
 * `node.description && ...` to `showDescription(...) && ...` without also having
 * to think about a two-step truthiness check.
 */
export function showDescription(
  text: string | undefined | null,
  min: number,
): string {
  return isThinDescription(text, min) ? "" : (text ?? "").trim();
}
