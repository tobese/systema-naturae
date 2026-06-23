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
