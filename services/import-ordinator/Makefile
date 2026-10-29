# Makefile for import-ordinator service
#
# Usage:
#   make lint           # Run all linters (Go + HTML)
#   make lint-go        # Run Go linter (golangci-lint)
#   make lint-html      # Run HTML linter (htmlhint)
#   make build          # Build the import-ordinator binary
#   make tidy           # Run go mod tidy
#   make test           # Run Go tests

GO := go
GOFMT := gofmt
GOLANGCI_LINT := golangci-lint
HTMLHINT := npx htmlhint

.PHONY: all build lint lint-go lint-html tidy test clean

all: build lint

build:
	$(GO) build -o /tmp/import-ordinator ./cmd/import-ordinator/

lint: lint-go lint-html

lint-go:
	@if command -v $(GOLANGCI_LINT) > /dev/null 2>&1; then \
		$(GOLANGCI_LINT) run ./...; \
	else \
		echo "golangci-lint not found. Install with: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"; \
		exit 1; \
	fi

lint-html:
	@if command -v npx > /dev/null 2>&1 && npx htmlhint --version > /dev/null 2>&1; then \
		npx htmlhint internal/**/*.html; \
	else \
		echo "htmlhint not found. Install with: npm install -g htmlhint"; \
		exit 1; \
	fi

tidy:
	$(GO) mod tidy

test:
	$(GO) test ./...

clean:
	rm -f /tmp/import-ordinator