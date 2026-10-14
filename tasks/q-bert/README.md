# q-bert — Sanity Queue Runner

**Host:** q-bert (agent session; works the local `systema-naturae` checkout on Macie / Tailscale)
**Pull first:** `git pull origin main` — this spec is only live once it has landed on `main`.

## Goal

Close the committed sanity queue (`sanity-issues.json`) until `make check` is green.

The committed snapshot is from the **2026-10-13 import batch**. After the push it
contains **9,723 open issues**:

| Issue | Count | Fixer |
|---|---:|---|
| `UNRESOLVED_TAXON` | 6,360 | name-parse-index rebuild + re-import (see note) |
| `ACCESSION_NAME` | 2,490 | `fix_fixture_nodes.py` (archaeal assembly accessions) |
| `HYBRID_RANK` | 637 | manual review (intergeneric hybrids, see `INTERGENERIC` in `sanity_scan.py`) |
| `DUPLICATE_GENUS` | 161 | `merge_duplicate_genera.py` |
| `SHORT_DESCRIPTION` | 64 | `fix_all_descriptions.py` |
| `SPECIES_ID_REPEATED` | 11 | `fix_duplicate_node_ids.py` |

> Two large buckets from the CLAUDE.md "expected state" note — `MISSING_COMMON_NAME`
> (2.24M) and `MISSING_CONTINENTS` (2.16M) across the COL/WFO/ITIS imports — are
> **out of scope** for this pass; they are bulk-fixable only via the source-import
> stage (`make patch-ids` / `fix_continents.py`), not family by family.

## Run order

**0. Refresh the (gitignored) working queue.**
`sanity-queue.json` is gitignored; the committed artifact is `sanity-issues.json`.
Regenerate both from the current tree:

```bash
python3 scripts/sanity_scan.py --write --archive
```

> `--no-parse-index` is NOT used: `UNRESOLVED_TAXON` needs `name-parse-index.jsonl`.
> That index is **2,989 files stale** after the WFO + ITIS imports, so rebuild it
> first or the UNRESOLVED counts will be inaccurate:
>
> ```bash
> make name-index        # POSTs every name to the GBIF parser — hours for 2.4M sp.
> ```
> Only rebuild if you are attacking the `UNRESOLVED_TAXON` bucket; the structural
> issues (DUPLICATE_GENUS, SPECIES_ID_REPEATED, SYNTHETIC_NAME) do not need it.

**1. Structural fixers (kingdom-wide, safest first).**
Each is idempotent and read-only-by-default; pass `--write` only where the script
supports it (check the docstring). The Makefile targets are the canonical entry
points — prefer them over calling scripts directly:

```bash
make fix-lineage                 # fixSpeciesLineage.py  — MISSING_LINEAGE
make fix-counts                  # resyncFamilyCounts.py — speciesCount drift
python3 scripts/fix_empty_genera.py  # EMPTY_GENUS
make fix-duplicates              # dedupeSpeciesAcrossFamilies.py — DUPLICATE_SPECIES
python3 scripts/merge_duplicate_genera.py   # DUPLICATE_GENUS (NOT fix_duplicates.py)
python3 scripts/fix_duplicate_node_ids.py  # SPECIES_ID_REPEATED
python3 scripts/fix_fixture_nodes.py       # ACCESSION_NAME, SYNTHETIC_NAME
python3 scripts/fix_subspecies.py          # MISSING_SUBSPECIES_COUNT
python3 scripts/fix_continents.py          # continent code expansion
python3 scripts/fix_redirect_descriptions.py
python3 scripts/fix_misattached_descriptions.py
python3 scripts/fix_all_descriptions.py    # SHORT_DESCRIPTION
```

> `fix_duplicates.py` **keep-first is wrong** — its header warns it deletes 27 real
> species (Ploceus alone appears twice with non-overlapping species). Use
> `merge_duplicate_genera.py` for duplicate *genera* (union by species id).

**2. Per-issue scan, verify, repeat.**
After each fixer pass:

```bash
python3 scripts/sanity_scan.py --issues DUPLICATE_GENUS,SPECIES_ID_REPEATED,ACCESSION_NAME,SYNTHETIC_NAME
```

**3. Rebuild + invariant gate.**
```bash
cd portal && SH_KINGDOM=animalia sh scripts/buildData.sh   # or SN_KINGDOM=<kingdom>
make verify                     # verifyTree invariants (non-zero exit on violation)
make check                      # full gate: tree.py selftest + verifyTree + scan (~4 min)
```

Large kingdoms need the 8 GB heap:
```bash
cd portal && NODE_OPTIONS=--max-old-space-size=8192 npx tsx scripts/buildData.ts
```

**4. Commit + push** (only after `make check` is green):
```bash
cd ../..
git add -A
git commit -m "fix: sanity queue pass — <N> issues closed across <families>"
git push
```

## Acceptance

- `git diff --stat HEAD~1` shows only `fixer`-touched family JSONs (+ the refreshed
  `sanity-issues.json`).
- `make check` exits 0.
- `git push` succeeds (no file >100 MB; the index rebuild in step 0 is gitignored).

## Notes

- `sanity-queue.json` and `name-parse-index.jsonl` are **gitignored** (scan
  snapshot / re-fetchable per-name-parser output) — never commit them.
- `sanity-issues.json` is the committed history snapshot; `--archive` rewrites it.
- `MISSING_COMMON_NAME` / `MISSING_CONTINENTS` are owned by the import pipeline,
  not this runner — hand those back to the importer (`make patch-ids`,
  `fix_continents.py` at source).
