# Import Pipeline Dashboard — Design Document

## Overview

A new web dashboard for the import pipeline, served by the `import-ordinator` Go service. Replaces `scripts/importLogServer.py` with a single Go binary that serves both the pipeline engine and its dashboard.

## Goals

1. **Single binary** — One Go process runs both the import pipeline orchestration and its dashboard (no separate Python importLogServer.py).
2. **Real-time status** — Read queue JSON files directly; no polling delay beyond the pipeline's own 60s cycle.
3. **Per-source visibility** — Show each source's stage, progress (species added/merged), and stage duration.
4. **Stuck detection** — Surface sources stuck in active stages (transforming/applying) using progress sidecar freshness + PID aliveness.
5. **Zero-config deployment** — Same `import-ordinator` binary serves both pipeline and dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              import-ordinator (Go)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Pipeline   │  │  Dashboard   │  │   Health     │  │
│  │   engine     │  │   server     │  │   (:8090)    │  │
│  │  (worker pool│  │  (HTML/JS)     │  │              │  │
│  │   3 workers) │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│           │               │               │             │
│           └───────────────┴───────────────┘             │
│                      reads queue JSON files             │
│                      reads progress sidecars            │
│                      reads import-log.jsonl             │
└─────────────────────────────────────────────────────────┘
```

## Data Sources

| Source | Purpose | Refresh |
|--------|---------|---------|
| `data/source-queue/<key>.json` | Per-source stage, stats, history | Every pipeline cycle (60s) |
| `data/import-log.jsonl` | Historical import events | On each dashboard request |
| `work/<slug>/transform.progress.json` | Transform progress (written by transformColChecklist.py) | Every 10s during transform |
| `work/<slug>/import.progress.json` | Apply progress (written by importTransformed.py) | Every 10s during apply |
| `data/source-queue/pipeline-events.jsonl` | Chronological pipeline events | On each dashboard request |

## Dashboard Pages

### 1. Overview Dashboard (`/`)
- Summary cards: total sources, by-stage counts, total species added/merged, active workers
- Recent activity feed (last 20 pipeline events)
- Quick links to stuck sources, error sources

### 2. Queue Table (`/queue`)
- Table of all sources with columns: Key, Title, Stage, Stage, Offered, Staged, Added, Merged, Refused, Refusal Rate, Families, Age in stage, Last event
- Filter by stage (candidate/downloaded/transforming/triaged/queued/applying/applied/declined/blocked/error)
- Sort by any column
- Color-coded stage badges (green=applied, yellow=transforming/applying, red=blocked/error)
- Click a source to see its detail page

### 3. Source Detail (`/source/<key>`)
- Source metadata (title, licence, size, archive path)
- Full stage history timeline
- Current stage stats (offered, staged, refused, refusal rate)
- Transform progress bar (if transforming)
- Apply progress bar (if applying)
- Import log entries for this source

### 4. Stuck Sources (`/stuck`)
- Sources stuck in transforming/applying beyond STUCK_TIMEOUT_MINUTES
- Shows last progress tick age, PID (if alive), archive path
- One-click reset to downloaded (for manual intervention)

### 5. Health (`/healthz`)
- Simple JSON: `{"status":"ok","workers":N}`

## UI Design

- Single-page HTML with inline CSS/JS (no external dependencies)
- Dark theme (matches existing portal aesthetic)
- Stage color coding:
  - applied: green (#3ddc84)
  - transforming/applying: yellow (#f5c45e)
  - blocked/error: red (#ff5c5c)
  - downloaded/queued: dim gray (#8a909c)
- Progress bars use CSS transitions
- Auto-refresh every 30 seconds (configurable via query param)
- Responsive table (scrollable horizontally)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/queue` | GET | JSON of all queue entries |
| `/source/<key>` | GET | JSON of single source + history |
| `/stuck` | GET | JSON of stuck sources |
| `/healthz` | GET | Health check |

## Implementation Plan

### Phase 1: Core Dashboard (Day 1)
- Add `internal/dashboard/` package to import-ordinator
- HTML template with embedded CSS/JS
- `/`, `/queue`, `/source/<key>`, `/healthz` endpoints
- Read queue JSON files directly
- Start server on port 8090 (configurable)

### Phase 2: Progress Tracking (Day 2)
- Read progress sidecar files for transforming/applying sources
- Show progress bars in queue table and source detail
- Stuck detection based on progress freshness

### Phase 3: Import Log (Day 3)
- Read `data/import-log.jsonl` for historical import events
- Show per-source import log on detail page
- Aggregate stats on overview (total added/merged)

### Phase 4: Actions (Day 4)
- Reset stuck source to downloaded (POST)
- Re-queue declined/blocked source (POST)
- Trigger refill (POST)

## Code Structure

```
services/import-ordinator/
├── cmd/import-ordinator/main.go
├── internal/
│   ├── dashboard/
│   │   ├── dashboard.go       # HTTP handlers
│   │   ├── template.go        # HTML template
│   │   └── model.go           # Dashboard data models
│   ├── queue/queue.go         # Queue store (existing)
│   ├── transform/transform.go # Transform runner (existing)
│   ├── apply/apply.go         # Apply runner (existing)
│   ├── download/download.go   # Download runner (existing)
│   └── worker/worker.go       # Pipeline worker (existing)
└── go.mod
```

## Integration with Existing Pipeline

The dashboard shares the same `queue.Store` instance as the worker pipeline. Both read from the same JSON files on disk, so the dashboard always reflects the current queue state. The orchestrator's `run_pass()` loop updates the queue files, and the dashboard reads them on each request.

## Deployment

Replace `scripts/importLogServer.py` with:
```bash
cd services/import-ordinator
IMPORTWRITE_URL=http://localhost:8089 SN_SOURCES_ROOT=/Volumes/MacieExternal/sources \
  SN_SOURCES_DB=/Users/tb/Dev/systema-naturae WORKERS=3 \
  go run ./cmd/import-ordinator --loop --port 8090
```

The same binary serves both the pipeline engine and the dashboard dashboard.

## Future Enhancements

- Per-source logs (stream transform/apply stdout)
- Retry failed sources with one click
- Export queue state to JSON/CSV
- Graph of species added over time
- Integration with importwrite service health check