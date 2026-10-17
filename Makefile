.PHONY: dev dev-daemon build data typecheck lint docker enrich species-parquet \
         name-index name-index-status verify verify-import triage \
         triage-sample serve fix-lineage fix-counts fix-duplicates check count \
         idmap patch-ids fill-authority-ids authority-index sources-report

# The pre-commit gate. `tree.py` first because it is a second and fails in
# milliseconds, then the invariants. Order matters: tree.py's selftest is the
# only thing that can catch a traversal being edited wrongly, and every other
# check now depends on it.
#
# Costs about four minutes, almost all of it JSON parsing, so this is cheap
# enough to run before every commit rather than only before an import. What it
# is FOR: today a bad import is caught at the next audit, which is how 980,786
# wrong lineages survived until 2026-10-05 and how 27 fungi families kept a
# stale speciesCount of 11 while their files held 1,220.
check:
	@python3 scripts/tree.py
	@python3 scripts/verifyTree.py
	@python3 scripts/sanity_scan.py taxonomy
	@echo "all checks passed"

# Flat projection of the tree for ad-hoc questions: "which families gained
# species in the last import", "how many species per kingdom have a stored
# description". Derived and gitignored, rebuilt in ~82s, never the source of
# truth. The only thing here that needs duckdb, which is not a project
# dependency -- PARQUET_PY overrides the interpreter if it lives in a venv.
#
#   make species-parquet PARQUET_PY=.venv-parquet/bin/python
PARQUET_PY ?= python3
species-parquet:
	@$(PARQUET_PY) scripts/buildSpeciesParquet.py $(ARGS)

count:
	@$(PARQUET_PY) scripts/countIds.py $(ARGS)

# Recount where the tree's content came from, per kingdom and in total, and
# write portal/public/data/sources-report.json — the table the portal's Sources
# modal renders. Two tallies, because the tree records two things:
# sourcedFrom (provenance of names and descriptions, 4.03M nodes) and sourceIds
# (which dataset supplied the name, 5.84M entries). Counts come from the tree;
# licences come from the manifest on the external volume, so an unmounted volume
# yields counts without licences rather than an error.
#
# Costs ~35s, nearly all of it parsing 18,509 family files. Run after an import:
# docs/data-sources.md counts are transcribed from this output by hand, and the
# last three imports left them describing a tree that no longer exists.
sources-report:
	cd portal && npx tsx scripts/aggregateSources.ts

# Build the species_id_map staging table from GBIF cache + wiki-images.json.
# One row per (scientific_name, source), deduplicated by confidence.
#   make idmap
#   make idmap PARQUET_PY=.venv-parquet/bin/python
idmap:
	@$(PARQUET_PY) scripts/buildIdMap.py $(ARGS)

# Add COL taxonIDs to species_id_map, from the COL DwCA archive.
#   make col-idmap
col-idmap:
	@$(PARQUET_PY) scripts/buildColIdMap.py $(ARGS)

# Add WFO identifiers to species_id_map, from the WFO Plant List archive.
#   make wfo-idmap
wfo-idmap:
	@$(PARQUET_PY) scripts/buildWfoIdMap.py $(ARGS)

# Add ITIS TSNs to species_id_map, from the ITIS archive.
#   make itis-idmap
itis-idmap:
	@$(PARQUET_PY) scripts/buildItisIdMap.py $(ARGS)

# Apply species_id_map to family JSON files: writes sourceIds/authorityIds
# to each species. Run after `make idmap` and before `make species-parquet`.
#   make patch-ids
#   make patch-ids --dry-run
patch-ids:
	@$(PARQUET_PY) scripts/patchFamilyIds.py $(ARGS)

# Derive authorityIds from sourceIds wherever it is missing. Closes the gap
# left by patch-ids, which only stamps authorityIds on species whose name is
# in species_id_map. Species that already carried sourceIds from an earlier
# backfillSourceIds.py run get their authorityIds here.
#   make fill-authority-ids
#   make fill-authority-ids --dry-run
fill-authority-ids:
	@$(PARQUET_PY) scripts/fillAuthorityIds.py $(ARGS)

# (kingdom, authority, key) -> species, for merge_family's cross-family
# duplicate gate. merge_family rebuilds this itself whenever it is stale (any
# family file newer than the index), so this target is for forcing a rebuild
# on demand -- after an import, or to check what it holds.
#   make authority-index          # rebuild unconditionally
#   make authority-index ARGS=--stats
authority-index:
	@python3 scripts/authorityIndex.py --build $(ARGS)

dev:
	cd portal && npm run dev

dev-daemon:
	cd portal && nohup npx vite --host > /tmp/vite-dev.log 2>&1 &
	@echo "Vite started (PID $$$$!) — log: /tmp/vite-dev.log"

build:
	cd portal && npm run build

data:
	cd portal && sh scripts/buildData.sh
	@$(MAKE) --no-print-directory name-index-status

# portal/data/name-parse-index.jsonl is a snapshot of every species name, taken
# at a moment and gitignored, so nothing in CI notices it drifting. It drifts on
# every import, and it has been wrong in both directions: it scored 15,563
# Cranefly species as new when 15,191 were held, and 13,347 of 16,371 ILDIS
# species as held when the tree holds 64. `data` reports rather than rebuilds,
# because rebuilding is a network job -- parseAllNames.py POSTs every name to
# GBIF's parser at ~113/s on one connection, hours for the 2.4M the tree holds.
name-index-status:
	@python3 scripts/nameIndexStatus.py || true

# The tree's data invariants, asserted rather than eyeballed. Every serious bug
# found importing sources in Oct 2026 produced a plausible number instead of an
# error, which is why none of them were caught by the test suite: a counter that
# read only one of six kingdoms reported "0 understated" while 574 nodes in the
# other five were wrong, and an importer labelled its already-on-disk count
# "unparseable" so a run read as if 40% of a dataset had failed to parse.
# Non-zero exit on violation, so CI can run it.
verify:
	@python3 scripts/verifyTree.py

# Gate a run that has just applied. Adds the refusal-rate check, which is the
# number no exit code has ever caught: WFO refused 0.26% and ITIS 5.5%, both
# healthy, while a run refusing 60% prints the same shape of output and leaves
# the tree with a fifth of its potential. Importers append to
# data/import-log.jsonl so this reads numbers rather than scraped stdout.
verify-import:
	@python3 scripts/verifyTree.py --after-import $(ARGS)

fix-lineage:
	@python3 scripts/fixSpeciesLineage.py $(ARGS)

fix-counts:
	@python3 scripts/resyncFamilyCounts.py $(ARGS)

fix-duplicates:
	@python3 scripts/dedupeSpeciesAcrossFamilies.py $(ARGS)

# Triage a ChecklistBank dataset before downloading it. TAXASERVE makes this an
# API-only measurement of the whole accepted list rather than a 600-name sample:
# on an alphabetical list the sample said WFO was 66.2% held when the true
# figure was 43.8%, which is 23 points of bias on a go/no-go decision.
#
#   make triage KEYS="2004 2144"              exact, minutes, no download
#   make triage-sample KEYS=1018               600-name sample, seconds
#
# Set RANK=GENUS for a register of genera: IRMNG holds 269,528 of them and 2
# species, and sampled at species rank it reported a confident 100% already-held
# from a two-name sample.
triage:
	@TAXASERVE="$${TAXASERVE:-http://127.0.0.1:9882}" \
	  python3 scripts/apiOverlapReport.py $(KEYS) --rank $${RANK:-SPECIES}

triage-sample:
	@TAXASERVE="$${TAXASERVE:-http://127.0.0.1:9882}" \
	  python3 scripts/sampleDatasetOverlap.py $(KEYS) --rank $${RANK:-SPECIES}

# The in-memory taxonomy index that `triage` uses. Reads 2.5GB of family JSON
# once (44s) so the tools above stop re-reading it per query.
serve:
	@python3 scripts/taxaserve.py --port $${PORT:-9882}

name-index:
	python3 scripts/parseAllNames.py $(ARGS)

# Migrate the monolith name-parse-index.jsonl into per-family sidecars under
# portal/data/name-parse-index/, plus a manifest. One-time operation; after this
# parseAllNames.py --split writes sidecars directly.
split-name-index:
	python3 scripts/splitNameIndex.py $(ARGS)

# Sync per-family name-parse-index sidecars between Macie and q-bert over SSH.
# Only sidecars whose manifest mtime/size differ are transferred.
sync-name-index-to-qbert:
	python3 scripts/syncNameIndex.py --to q-bert $(ARGS)

sync-name-index-from-qbert:
	python3 scripts/syncNameIndex.py --from q-bert $(ARGS)

typecheck:
	cd portal && npm run typecheck

lint:
	cd portal && npm run lint

import:
	OLLAMA_MODEL=qwen2.5:3b cd portal && npm run import $(ARGS)

import-steamie:
	OLLAMA_HOST=steamie.local OLLAMA_MODEL=qwen2.5-coder:7b OLLAMA_TIMEOUT=600000 cd portal && npm run import $(ARGS)

import-biggie:
	OLLAMA_HOST=biggie.local OLLAMA_MODEL=qwen2.5-coder:3b OLLAMA_NUM_GPU=0 cd portal && npm run import $(ARGS)

fetch:
	cd portal && npm run fetch $(ARGS)

cache-gbif:
	cd portal && npm run cache-gbif

docker:
	docker build -t systema-naturae .

SHELL := /bin/zsh
PATH := $(HOME)/.nvm/versions/node/v23.3.0/bin:/usr/local/bin:/opt/homebrew/bin:$(PATH)

# One pass over the whole kingdom, not one per class. The old loop walked 11
# hard-coded class directories and staged `git add -A $$cls/`, which under
# taxonomy/<kingdom>/<phylum>/<class>/ matched nothing: `git add` failed with
# "pathspec 'aves/' did not match any files", the && chain aborted before the
# commit, and the for-loop used ';' so it carried on to the next class. The
# enrichment ran, the commits were lost, and the final `git push` pushed
# whatever happened to be staged. enrichFromWikipedia.ts now derives its class
# list from the taxonomy and walks taxonomy/animalia/ directly.
SN_KINGDOM ?= animalia

enrich:
	@echo "=== Enriching $$(SN_KINGDOM) from Wikipedia ==="
	cd portal && SN_KINGDOM=$(SN_KINGDOM) npx tsx scripts/enrichFromWikipedia.ts
	cd portal && SN_KINGDOM=$(SN_KINGDOM) sh scripts/buildData.sh
	cd .. && git add -A && git commit -m "Enrich $$(SN_KINGDOM) with Wikipedia" || echo "  nothing to commit"
	@git push
	@$(MAKE) --no-print-directory name-index-status
