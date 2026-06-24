.PHONY: dev build data typecheck lint

dev:
	cd portal && npm run dev

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
	OLLAMA_HOST=biggie.local OLLAMA_MODEL=qwen2.5-coder:3b cd portal && npm run import $(ARGS)

fetch:
	cd portal && npm run fetch $(ARGS)

cache-gbif:
	cd portal && npm run cache-gbif

SHELL := /bin/zsh
PATH := $(HOME)/.nvm/versions/node/v23.3.0/bin:/usr/local/bin:/opt/homebrew/bin:$(PATH)

enrich:
	@for cls in aves mammalia reptilia amphibia actinopterygii chondrichthyes insecta arachnida asteroidea echinoidea holothuroidea; do \
	  echo "=== Enriching $$cls ==="; \
	  cd portal && npx tsx scripts/enrichFromWikipedia.ts --class $$cls; \
	  cd portal && sh scripts/buildData.sh; \
	  cd .. && git add -A $$cls/ portal/scripts/ portal/data/ && git commit -m "Enrich $$cls with Wikipedia" --allow-empty; \
	done; \
	git push
