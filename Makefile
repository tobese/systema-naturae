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

fetch:
	cd portal && npm run fetch $(ARGS)

cache-gbif:
	cd portal && npm run cache-gbif

enrich:
	@for cls in aves mammalia reptilia amphibia actinopterygii chondrichthyes insecta arachnida asteroidea echinoidea holothuroidea; do \
	  echo "=== Enriching $$cls ==="; \
	  cd portal && npx tsx scripts/enrichFromWikipedia.ts --class $$cls; \
	  cd portal && sh scripts/buildData.sh; \
	  cd .. && git add -A aves/ $$cls/ portal/data/ && git commit -m "Enrich $$cls with Wikipedia" --allow-empty; \
	done; \
	git push
