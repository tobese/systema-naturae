# q-bert — Bacteria + Viruses import

**Host:** q-bert (agent session; works the local `systema-naturae` checkout on
Steamie / Tailscale)
**Pull first:** `git pull origin main` — this spec is only live once it lands.

## Goal

Import the two triaged sources that carry Bacteria and Viruses as real
divisions. They are the only candidates in `scripts/sourcesManifest.py` that do:
COL holds prokaryotes and viruses in 17 clades at kingdom rank, which is not a
tree we can render, and every other source is eukaryote-only.

| Source | Status | What it offers | Importer |
|---|---|---|---|
| `ncbi-taxonomy` | assessed, 2026-10-08 | 197,971 accepted species, 44,946 held, **120,665 not held**; 3,120 of 10,907 families absent | `importNcbiBacteriaViruses.py` |
| `gtdb` r232 | assessed, downloaded | 242,895 accepted name usages: 189,801 bacterial in 3,967 families + 10,122 archaeal, 125 phyla, two domains, **no kingdom rank** | `importGtdbBacteria.py`, `importGtdbArchaea.py` |

`ictv-msl` is already applied — nothing to do there.

## Also on the Macie plate (do these too if time permits)

These are eukaryote sources that were assessed on Macie but never imported;
they are downloaded and ready, and the converters are committed:

| Source | Status | Importer |
|---|---|---|
| `checklistbank-1046` GloBIS | CC BY, **727 new** butterfly species across Lycaenidae/Papilionidae/Pieridae | `importColChecklist.py <archive>` (ILDIS shape, reads directly) |
| `checklistbank-312616` COL China 2026 | 148,081 distinct names, no rank column | `colchinaToColDP.py --apply` then `importColChecklist.py archives/colchina/NameUsage.tsv` |
| `checklistbank-1028` Species Fungorum | 30.1% new, blocked on permission | needs one email to Index Fungorum first |
| `checklistbank-304756` AlgaeBase | deferred on CC BY-NC | needs a standing-policy call |

`archiveOverlap.py` now reads gzip'd tar archives as well as zip, so any
ChecklistBank dataset whose endpoint answers with a tar measures correctly.

## Run order

**0. Pull + sync.**
```bash
git pull origin main
```
The Macie side is actively importing; this repo moves. Re-pull before every
batch so you are not working on a stale tree.

**1. NCBI Bacteria + Viruses.**
```bash
python3 scripts/importNcbiBacteriaViruses.py --apply
```
Dry run first (`--apply` omitted) to see the counts. NCBI is the one that
carries Bacteria and Viruses as real divisions with real authorities, which is
exactly what COL will not give.

**2. GTDB Bacteria, then Archaea.**
```bash
python3 scripts/importGtdbBacteria.py --apply
python3 scripts/importGtdbArchaea.py --apply
```
GTDB's archive is already on the sources volume. Its 242,895 name usages are
189,801 bacterial species in 3,967 families plus 10,122 archaeal across 125
phyla, and — the fact that decides its placement — it has **no kingdom rank
anywhere**. COL's eight prokaryote clades (Bacillati, Pseudomonadati,
Thermotogati, Fusobacteriati, Methanobacteriati, Thermoproteati, Nanobdella…)
are kingdom-rank clades, not kingdoms, and grafting GTDB under them is the
resolution. Do not graft it at kingdom rank.

**3. Rebuild + verify.**
```bash
cd portal && SN_KINGDOM=archaea NODE_OPTIONS=--max-old-space-size=8192 npx tsx scripts/buildData.sh
cd portal && SN_KINGDOM=bacteria NODE_OPTIONS=--max-old-space-size=8192 npx tsx scripts/buildData.sh
cd .. && make verify
```
Large kingdoms need the 8 GB heap. `SN_KINGDOM` selects the kingdom; everything
else comes from `kingdom-config.json`.

**4. Commit + push** (chunked — see `scripts/commit-chunks.sh`):
```bash
scripts/commit-chunks.sh "Import NCBI bacteria/viruses + GTDB"
```

## Notes

- `portal/data/name-parse-index.jsonl` (586 MB) and
  `portal/data/sanity-queue.json` are gitignored — never commit them.
- `portal/data/itis-vernacular-index.json` is gitignored as of
  `dfaa97387ee`. Derived indexes stay out of history.
- After a significant import, refresh the gap reports:
  ```bash
  cd portal
  npx tsx scripts/findGaps.ts
  npx tsx scripts/reportPhyla.ts
  npx tsx scripts/generateGapTasks.ts
  ```
- `sanity-issues.json` is the committed history snapshot; refresh with
  `python3 scripts/sanity_scan.py --write --archive` when the tree changes.

## Acceptance

- `git diff --stat HEAD~1` shows only importer-touched family JSONs.
- `make verify` exits 0.
- `git push` succeeds.