// Command import-ordinator is the single-writer daemon for the import pipeline.
//
// It watches the source queue (data/source-queue/*.json) and drives sources
// through: candidate → downloaded → transforming → triaged → queued → applying → applied.
//
// Transform, apply, and download steps run as subprocesses with hard timeouts
// so a hung script can never block the pipeline forever. Progress is tracked
// via progress sidecar files written by those scripts, allowing check_stuck()
// to distinguish genuinely stalled processes from legitimately long-running ones.
//
// Worker goroutines process sources in parallel, bounded by the WORKERS
// environment variable (default 1 -- route_species() on a large archive
// holds gigabytes, so raise it only with memory to spare).
//
// Each pass holds scripts/maintenanceLock.py's lock (non-blocking; a busy
// lock skips the pass) while it drains the queue, then runs
// `pipelineOrchestrator.py --side-tasks` for the stages this daemon does
// not implement: refill/discovery, needs-rerun and the pending-family sweep.
// Do not run pipelineOrchestrator.py --loop alongside it.
//
// Usage:
//
//	go run ./cmd/import-ordinator          # run once, then exit
//	go run ./cmd/import-ordinator --loop   # keep polling every 60s
//
// Environment variables:
//
//	SN_SOURCES_ROOT   root of the sources volume (default /Volumes/MacieExternal/sources)
//	SN_SOURCES_DB     root of the repo (default current directory)
//	IMPORTWRITE_URL   URL of the importwrite service (default http://localhost:8089)
//	WORKERS           number of concurrent workers (default 1)
//	TRANSFORM_TIMEOUT minutes for transform timeout (default 30)
//	APPLY_TIMEOUT     minutes for apply timeout (default 30)
//	DOWNLOAD_TIMEOUT  minutes for download timeout (default 60)
//	SIDE_TASK_TIMEOUT minutes for the Python side tasks (default 120)
//	PORT              HTTP dashboard port (default 8090)

package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"systema-naturae/import-ordinator/internal/dashboard"
	"systema-naturae/import-ordinator/internal/gbifdb"
	"systema-naturae/import-ordinator/internal/worker"
)

func main() {
	loop := flag.Bool("loop", false, "keep polling every 60s")
	port := flag.String("port", "8090", "HTTP dashboard port")
	flag.Parse()

	sourcesRoot := os.Getenv("SN_SOURCES_ROOT")
	if sourcesRoot == "" {
		sourcesRoot = "/Volumes/MacieExternal/sources"
	}

	// Initialize GBIF datasets
	if err := gbifdb.Init(sourcesRoot, 1000); err != nil {
		log.Printf("gbifdb init warning: %v", err)
	}

	repoRoot := os.Getenv("SN_SOURCES_DB")
	if repoRoot == "" {
		wd, err := os.Getwd()
		if err != nil {
			log.Fatalf("cannot determine working directory: %v", err)
		}
		repoRoot = wd
	}

	importWriteURL := os.Getenv("IMPORTWRITE_URL")
	if importWriteURL == "" {
		importWriteURL = "http://localhost:8089"
	}

	workers := 1
	if w := os.Getenv("WORKERS"); w != "" {
		if n, err := fmt.Sscanf(w, "%d", &workers); err != nil || n != 1 || workers < 1 {
			workers = 1
		}
	}

	transformTimeout := 30 * time.Minute
	if t := os.Getenv("TRANSFORM_TIMEOUT"); t != "" {
		if d, err := time.ParseDuration(t + "m"); err == nil {
			transformTimeout = d
		}
	}

	applyTimeout := 30 * time.Minute
	if t := os.Getenv("APPLY_TIMEOUT"); t != "" {
		if d, err := time.ParseDuration(t + "m"); err == nil {
			applyTimeout = d
		}
	}

	downloadTimeout := 60 * time.Minute
	if t := os.Getenv("DOWNLOAD_TIMEOUT"); t != "" {
		if d, err := time.ParseDuration(t + "m"); err == nil {
			downloadTimeout = d
		}
	}

	sideTaskTimeout := 120 * time.Minute
	if t := os.Getenv("SIDE_TASK_TIMEOUT"); t != "" {
		if d, err := time.ParseDuration(t + "m"); err == nil {
			sideTaskTimeout = d
		}
	}

	pollInterval := 60 * time.Second

	// Create the pipeline
	pipeline := worker.NewPipeline(
		worker.Config{
			SourcesRoot:      sourcesRoot,
			RepoRoot:         repoRoot,
			ImportWriteURL:   importWriteURL,
			Workers:          workers,
			TransformTimeout: transformTimeout,
			ApplyTimeout:     applyTimeout,
			DownloadTimeout:  downloadTimeout,
			SideTaskTimeout:  sideTaskTimeout,
			PollInterval:     pollInterval,
		},
	)

	// Create the dashboard
	dash := dashboard.NewDashboard(pipeline.Store())

	// Context for graceful shutdown
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// HTTP server with dashboard and health endpoints
	mux := http.NewServeMux()
	mux.HandleFunc("/", dash.HandleIndex)
	mux.HandleFunc("/queue", dash.HandleQueue)
	mux.HandleFunc("/source/", dash.HandleSource)
	mux.HandleFunc("/stuck", dash.HandleStuck)
	mux.HandleFunc("/gbif", dash.HandleGBIF)
	mux.HandleFunc("/gbif/", dash.HandleGBIFToggle)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	addr := ":" + *port
	log.Printf("import-ordinator starting: %d workers, poll every %s, dashboard on :%s", workers, pollInterval, *port)

	// Run pipeline in background goroutine
	go func() {
		if *loop {
			log.Printf("import-ordinator pipeline loop starting")
			pipeline.RunLoop(ctx)
		} else {
			log.Println("import-ordinator running single pass")
			pipeline.RunOnce(ctx)
		}
	}()

	// HTTP server
	srv := &http.Server{
		Addr:    addr,
		Handler: mux,
	}

	// Run HTTP server in goroutine
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("HTTP server error: %v", err)
		}
	}()

	// Wait for context cancellation (SIGINT/SIGTERM)
	<-ctx.Done()
	log.Println("shutting down...")

	// Graceful shutdown with timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Printf("HTTP server shutdown error: %v", err)
	}

	pipeline.Stop()
	log.Println("import-ordinator stopped")
}
