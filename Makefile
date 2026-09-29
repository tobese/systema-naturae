.PHONY: dev dev-daemon build data typecheck lint docker

dev:
	cd portal && npm run dev

dev-daemon:
	cd portal && nohup npx vite --host > /tmp/vite-dev.log 2>&1 &
	@echo "Vite started (PID $$$$!) — log: /tmp/vite-dev.log"

build:
	cd portal && npm run build

data:
	cd portal && sh scripts/buildData.sh

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
