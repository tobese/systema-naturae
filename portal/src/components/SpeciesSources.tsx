import type { TaxonNode } from "@shared/types";
import { useContributorsIndex } from "../hooks/useContributorsIndex";

const CLB_KEY = /^checklistbank-(\d+)$/;

/**
 * The datasets a species record came from, read from its `sourceIds` and
 * named through contributors-index.json. A ChecklistBank dataset links to
 * the record itself; others to the dataset.
 */
export default function SpeciesSources({ node }: { node: TaxonNode }) {
  const index = useContributorsIndex();
  if (!index || !node.sourceIds) return null;

  const rows = new Map<string, { title: string; href: string | null; institution: string | null; licence: string | null }>();
  let unrecorded = false;
  for (const [key, value] of Object.entries(node.sourceIds)) {
    const ds = index.keyMap[key];
    if (!ds) continue;
    if (ds.startsWith("unrecorded:")) { unrecorded = true; continue; }
    if (rows.has(ds)) continue;
    const meta = index.datasets[ds];
    const recordId = Array.isArray(value) ? value[0] : value;
    const clb = CLB_KEY.exec(ds);
    rows.set(ds, {
      title: meta?.title ?? ds,
      href: clb && recordId
        ? `https://www.checklistbank.org/dataset/${clb[1]}/taxon/${encodeURIComponent(recordId)}`
        : meta?.url ?? null,
      institution: meta?.institution && meta.institution !== meta.title ? meta.institution : null,
      licence: meta?.licence ?? null,
    });
  }
  if (rows.size === 0 && !unrecorded) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "#444", marginBottom: 4 }}>Sources</div>
      <ul style={{ padding: 0, margin: 0, listStyle: "none" }}>
        {[...rows.values()].map((r) => (
          <li key={r.title} style={{ fontSize: 12, lineHeight: 1.5, marginBottom: 3 }}>
            {r.href
              ? <a href={r.href} target="_blank" rel="noreferrer noopener" style={{ color: "#8a8ac0" }}>{r.title}</a>
              : <span style={{ color: "#aaa" }}>{r.title}</span>}
            {(r.institution || r.licence) && (
              <span style={{ color: "#555", fontSize: 11 }}>
                {" · "}{[r.institution, r.licence].filter(Boolean).join(" · ")}
              </span>
            )}
          </li>
        ))}
        {unrecorded && (
          <li style={{ fontSize: 11, color: "#555" }}>Also a ChecklistBank dataset not recorded on this species</li>
        )}
      </ul>
    </div>
  );
}
