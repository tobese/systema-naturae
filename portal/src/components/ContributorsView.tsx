import { useEffect, useMemo, useState } from "react";

/**
 * Who the tree's content came from, by institution.
 *
 * Reads `contributors-report.json`, written by `scripts/buildContributors.py`
 * (`make contributors`) from the species parquet and the ChecklistBank / GBIF
 * metadata of every dataset. Every name, link, logo, citation and licence
 * shown here is taken from those APIs or from data/contributors-overrides.json;
 * nothing is filled in by the portal.
 */
interface Dataset {
  id: string;
  title: string | null;
  alias?: string | null;
  url: string | null;
  doi: string | null;
  citation: string | null;
  licence: string | null;
  licenceNote: string | null;
  creators: string[];
  institution: string;
  section: string;
  version?: string | null;
  counts: { species: Record<string, number>; text: Record<string, number> };
  addedAtImport: number | null;
}

interface Institution {
  name: string | null;
  url: string | null;
  logo: string | null;
  self?: boolean;
}

interface Report {
  generatedAt: string;
  kingdoms: string[];
  totals: Record<string, number>;
  noProvenance: Record<string, number>;
  unrecorded: Record<string, Record<string, number>>;
  institutions: Record<string, Institution>;
  datasets: Record<string, Dataset>;
}

const SECTIONS: { id: string; heading: string; blurb: string }[] = [
  { id: "records", heading: "Species records", blurb: "Datasets that supplied species to the tree, counted by the species that carry the dataset's id." },
  { id: "text", heading: "Descriptions, names & media", blurb: "Text, common names and images shown alongside the species." },
  { id: "nomenclature", heading: "Nomenclature & authorities", blurb: "Used to check names, authorship and genus placement rather than to add species." },
];

const NUM = new Intl.NumberFormat("en-US");
const BASE = import.meta.env.BASE_URL ?? "/";

function inScope(counts: Record<string, number>, scope: string): number {
  if (scope === "all") return Object.values(counts).reduce((a, n) => a + n, 0);
  return counts[scope] ?? 0;
}

function weight(d: Dataset, scope: string): number {
  return inScope(d.counts.species, scope) || inScope(d.counts.text, scope);
}

export default function ContributorsView({ scope, setScope }: { scope: string; setScope: (s: string) => void }) {
  const [report, setReport] = useState<Report | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${BASE}data/contributors-report.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setReport)
      .catch(() => setFailed(true));
  }, []);

  const groups = useMemo(() => {
    if (!report) return null;
    const q = query.trim().toLowerCase();
    const bySection: Record<string, Map<string, Dataset[]>> = {};
    let hidden = 0;
    for (const d of Object.values(report.datasets)) {
      const counted = weight(d, scope) > 0;
      // Nomenclature sources carry no per-kingdom counts; datasets credited
      // only by their import record can't be placed in a kingdom.
      if (!counted && d.section !== "nomenclature" && scope !== "all") {
        if (d.addedAtImport) hidden++;
        continue;
      }
      if (!counted && d.section !== "nomenclature" && !d.addedAtImport) continue;
      const inst = report.institutions[d.institution];
      if (q && ![d.title, d.alias, inst?.name, ...d.creators].some((s) => s?.toLowerCase().includes(q))) continue;
      const m = (bySection[d.section] ??= new Map());
      m.set(d.institution, [...(m.get(d.institution) ?? []), d]);
    }
    const out = SECTIONS.map((s) => {
      const rows = [...(bySection[s.id]?.entries() ?? [])].map(([iid, ds]) => ({
        iid,
        datasets: ds.sort((a, b) => weight(b, scope) - weight(a, scope) || (b.addedAtImport ?? 0) - (a.addedAtImport ?? 0)),
        total: ds.reduce((a, d) => a + weight(d, scope), 0),
      }));
      rows.sort((a, b) => b.total - a.total || (report.institutions[a.iid]?.name ?? "").localeCompare(report.institutions[b.iid]?.name ?? ""));
      return { ...s, rows };
    });
    return { sections: out, hidden };
  }, [report, scope, query]);

  if (failed) {
    return (
      <p style={{ color: "#a08050", fontSize: 13, lineHeight: 1.6 }}>
        The contributors report has not been generated. Run{" "}
        <code style={{ color: "#c0c0d8" }}>make contributors</code> in the repository root.
      </p>
    );
  }
  if (!report || !groups) return <p style={{ color: "#666", fontSize: 13 }}>Loading…</p>;

  const unrecorded = Object.values(report.unrecorded).reduce((a, c) => a + inScope(c, scope), 0);
  const noProv = inScope(report.noProvenance, scope);

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "14px 0 0" }}>
        <select
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          style={{ background: "#14161f", color: "#c0c0d8", border: "1px solid #1e2030", borderRadius: 6, padding: "4px 8px", fontSize: 12 }}
        >
          {[...report.kingdoms].sort().map((k) => <option key={k} value={k}>{k}</option>)}
          <option value="all">All kingdoms</option>
        </select>
        <span style={{ color: "#666", fontSize: 12 }}>{NUM.format(inScope(report.totals, scope))} species</span>
      </div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search institutions, datasets, authors…"
        style={{ width: "100%", boxSizing: "border-box", margin: "12px 0 0", background: "#14161f", color: "#c0c0d8", border: "1px solid #1e2030", borderRadius: 6, padding: "6px 10px", fontSize: 12 }}
      />
      {groups.sections.map((s) => s.rows.length > 0 && (
        <div key={s.id} style={{ marginTop: 20 }}>
          <div style={{ fontSize: 11, color: "#c0c0d8", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            {s.heading} <span style={{ color: "#444" }}>· {s.rows.length}</span>
          </div>
          <p style={{ margin: "4px 0 8px", color: "#555", fontSize: 11, lineHeight: 1.5 }}>{s.blurb}</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {s.rows.map((r) => (
              <InstitutionCard
                key={r.iid}
                inst={report.institutions[r.iid]}
                datasets={r.datasets}
                total={r.total}
                scope={scope}
                open={open === `${s.id}/${r.iid}`}
                toggle={() => setOpen(open === `${s.id}/${r.iid}` ? null : `${s.id}/${r.iid}`)}
              />
            ))}
          </div>
        </div>
      ))}
      <p style={{ color: "#555", fontSize: 11, lineHeight: 1.6, margin: "18px 0 0" }}>
        {unrecorded > 0 && <>{NUM.format(unrecorded)} species carry only the generic ChecklistBank id, with no record of which dataset supplied them. </>}
        {noProv > 0 && <>{NUM.format(noProv)} species record no source at all. </>}
        {groups.hidden > 0 && <>{groups.hidden} more datasets are credited from their import record only; see All kingdoms. </>}
        Metadata from ChecklistBank and GBIF, {report.generatedAt.slice(0, 10)}.
      </p>
    </>
  );
}

function Logo({ inst }: { inst: Institution | undefined }) {
  const [broken, setBroken] = useState(false);
  const box = { width: 40, height: 40, flex: "0 0 40px", borderRadius: 6, background: "#f4f4f6", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" } as const;
  if (inst?.logo && !broken) {
    return (
      <div style={box}>
        <img src={`${BASE}data/${inst.logo}`} alt="" loading="lazy" onError={() => setBroken(true)}
             style={{ maxWidth: 36, maxHeight: 36, objectFit: "contain" }} />
      </div>
    );
  }
  const initials = (inst?.name ?? "?").split(/\s+/).filter((w) => /^[A-Za-z]/.test(w)).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  return <div style={{ ...box, background: "#1a1c28", color: "#6666aa", fontSize: 13, letterSpacing: "0.05em" }}>{initials || "?"}</div>;
}

function InstitutionCard({ inst, datasets, total, scope, open, toggle }: {
  inst: Institution | undefined;
  datasets: Dataset[];
  total: number;
  scope: string;
  open: boolean;
  toggle: () => void;
}) {
  const single = datasets.length === 1 && inst?.self;
  return (
    <div style={{ border: "1px solid #1a1c28", borderRadius: 8, background: open ? "#12141c" : "transparent" }}>
      <div onClick={toggle} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 10px", cursor: "pointer" }}>
        <Logo inst={inst} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: "#c0c0d8", fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {inst?.url ? (
              <a href={inst.url} target="_blank" rel="noreferrer noopener" onClick={(e) => e.stopPropagation()} style={{ color: "#a0a0d0", textDecoration: "none" }}>
                {inst.name}
              </a>
            ) : inst?.name}
          </div>
          <div style={{ color: "#555", fontSize: 11 }}>
            {single ? (datasets[0].licence ?? "licence not recorded") : `${datasets.length} dataset${datasets.length === 1 ? "" : "s"}`}
          </div>
        </div>
        <div style={{ color: "#888", fontSize: 12, fontVariantNumeric: "tabular-nums", textAlign: "right" }}>
          {total > 0 ? <>{NUM.format(total)} <span style={{ color: "#555", fontSize: 10 }}>species</span></> : null}
        </div>
        <span style={{ color: "#444", fontSize: 10 }}>{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div style={{ padding: "0 10px 10px 62px", display: "flex", flexDirection: "column", gap: 10 }}>
          {datasets.map((d) => <DatasetRow key={d.id} d={d} scope={scope} />)}
        </div>
      )}
    </div>
  );
}

function LicenceBadge({ licence }: { licence: string | null }) {
  const nc = !!licence && /\bNC\b/i.test(licence);
  const sa = !!licence && /\bSA\b/i.test(licence);
  return (
    <span style={{
      fontSize: 10, padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap",
      border: `1px solid ${nc ? "#5a4a2a" : "#24263a"}`, color: nc ? "#c0a060" : licence ? "#8a8ab0" : "#7a6040",
    }} title={sa ? "Share-alike: adaptations must carry the same licence" : nc ? "Non-commercial" : undefined}>
      {licence ?? "licence not recorded"}
    </span>
  );
}

function DatasetRow({ d, scope }: { d: Dataset; scope: string }) {
  const species = inScope(d.counts.species, scope);
  const text = inScope(d.counts.text, scope);
  return (
    <div style={{ fontSize: 12, lineHeight: 1.55 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
        {d.url ? (
          <a href={d.url} target="_blank" rel="noreferrer noopener" style={{ color: "#8a8ac0" }}>{d.title ?? d.id}</a>
        ) : <span style={{ color: "#c0c0d8" }}>{d.title ?? d.id}</span>}
        {d.alias && d.alias !== d.title && <span style={{ color: "#555", fontSize: 11 }}>{d.alias}</span>}
        <LicenceBadge licence={d.licence} />
      </div>
      <div style={{ color: "#666", fontSize: 11 }}>
        {species > 0 && <>{NUM.format(species)} species</>}
        {species > 0 && text > 0 && " · "}
        {text > 0 && <>{NUM.format(text)} names/descriptions</>}
        {species === 0 && text === 0 && d.addedAtImport ? <>{NUM.format(d.addedAtImport)} species added at import, not tagged per species</> : null}
        {d.doi && <> · <a href={`https://doi.org/${d.doi}`} target="_blank" rel="noreferrer noopener" style={{ color: "#6a6a99" }}>doi:{d.doi}</a></>}
        {d.version && <> · version {d.version}</>}
      </div>
      {d.citation && <div style={{ color: "#777", fontSize: 11, marginTop: 2 }}>{d.citation}</div>}
      {!d.citation && d.creators.length > 0 && <div style={{ color: "#666", fontSize: 11 }}>{d.creators.join(", ")}</div>}
      {d.licenceNote && <div style={{ color: "#5a5a66", fontSize: 10, marginTop: 2 }}>{d.licenceNote}</div>}
    </div>
  );
}
