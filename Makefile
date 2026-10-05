.PHONY: dev dev-daemon build data typecheck lint docker enrich \
        name-index name-index-status verify triage triage-sample serve

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
