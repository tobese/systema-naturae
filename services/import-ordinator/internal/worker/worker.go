// Package worker runs the import pipeline for individual sources.
package worker

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"systema-naturae/import-ordinator/internal/apply"
	"systema-naturae/import-ordinator/internal/download"
	"systema-naturae/import-ordinator/internal/maintlock"
	"systema-naturae/import-ordinator/internal/queue"
	"systema-naturae/import-ordinator/internal/runproc"
	"systema-naturae/import-ordinator/internal/transform"
)

// Config holds pipeline configuration.
type Config struct {
	SourcesRoot      string
	RepoRoot         string
	ImportWriteURL   string
	Workers          int
	TransformTimeout time.Duration
	ApplyTimeout     time.Duration
	DownloadTimeout  time.Duration
	SideTaskTimeout  time.Duration
	PollInterval     time.Duration
	// QueueDir defaults to <repo>/data/source-queue. q-bert's bacteria/viruses
	// ordinator keeps its own (SN_QUEUE_DIR), so the two machines' queue
	// files never meet in a merge.
	QueueDir string
	// NoDownload: work only from archives already on this machine; a source
	// without one waits rather than being fetched.
	NoDownload bool
	// NoSideTasks: skip pipelineOrchestrator.py --side-tasks (discovery,
	// needs-rerun, the pending-family sweep).
	NoSideTasks bool
}

// Pipeline runs the import pipeline.
type Pipeline struct {
	cfg   Config
	store *queue.Store
	dl    *download.Runner
	tr    *transform.Runner
	ap    *apply.Runner
	stop  chan struct{}
	done  chan struct{}
}

// NewPipeline creates a new pipeline.
func NewPipeline(cfg Config) *Pipeline {
	if cfg.Workers < 1 {
		cfg.Workers = 1
	}
	if cfg.QueueDir == "" {
		cfg.QueueDir = filepath.Join(cfg.RepoRoot, "data", "source-queue")
	}
	return &Pipeline{
		cfg:   cfg,
		store: queue.NewStore(cfg.QueueDir),
		dl: &download.Runner{
			SourcesRoot: cfg.SourcesRoot,
			Timeout:     cfg.DownloadTimeout,
		},
		tr: &transform.Runner{
			ScriptDir:   filepath.Join(cfg.RepoRoot, "scripts"),
			SourcesRoot: cfg.SourcesRoot,
			Timeout:     cfg.TransformTimeout,
		},
		ap: &apply.Runner{
			ScriptDir:   filepath.Join(cfg.RepoRoot, "scripts"),
			SourcesRoot: cfg.SourcesRoot,
			Timeout:     cfg.ApplyTimeout,
		},
		stop: make(chan struct{}),
		done: make(chan struct{}),
	}
}

// RunOnce runs a single pass: drain the queue under the maintenance lock,
// then hand the stages this daemon doesn't implement (refill/discovery,
// needs-rerun, pending-family sweep) to the Python orchestrator.
func (p *Pipeline) RunOnce(ctx context.Context) {
	// Same lock and same policy as pipelineOrchestrator.py: a maintenance
	// pass (dedupe/resync --apply) holds it for its whole run, so take a
	// non-blocking shot and skip this pass's writes rather than race it.
	lock, ok, err := maintlock.TryAcquire(filepath.Join(p.cfg.RepoRoot, "data", ".maintenance.lock"))
	if err != nil {
		fmt.Printf("maintenance lock error: %v -- skipping this pass\n", err)
		return
	}
	if !ok {
		fmt.Println("maintenance pass in progress -- skipping this pass's writes")
		return
	}
	p.drain(ctx)
	lock.Release()

	// Outside the lock: the Python side takes the same lock itself, and
	// flock on a second descriptor would fail even from our own child.
	if !p.cfg.NoSideTasks {
		p.runSideTasks(ctx)
	}
}

func (p *Pipeline) drain(ctx context.Context) {
	entries, err := p.store.Read()
	if err != nil {
		fmt.Printf("error reading queue: %v\n", err)
		return
	}

	// A source still in an active stage at the start of a pass was left
	// there by a run that died (this daemon processes every source to a
	// resting stage within the pass that picked it up).
	for _, key := range queue.SortKeys(entries) {
		e := entries[key]
		switch e.Stage {
		case queue.StageTransforming, queue.StageTriaged:
			p.store.SetStageReason(key, e, queue.StageDownloaded, "reset: left in "+string(e.Stage)+" by an interrupted run")
		case queue.StageApplying:
			p.store.SetStageReason(key, e, queue.StageQueued, "reset: left in applying by an interrupted run")
		}
	}

	sem := make(chan struct{}, p.cfg.Workers)
	var wg sync.WaitGroup
	for _, key := range queue.SortKeys(entries) {
		entry := entries[key]
		if !queue.CanProcess(entry.Stage) {
			continue
		}
		select {
		case <-ctx.Done():
			wg.Wait()
			return
		case sem <- struct{}{}:
		}
		wg.Add(1)
		go func(key string, entry *queue.Entry) {
			defer wg.Done()
			defer func() { <-sem }()
			p.processOne(ctx, key, entry)
		}(key, entry)
	}
	wg.Wait()
}

func (p *Pipeline) runSideTasks(ctx context.Context) {
	fmt.Println("\n-- side tasks (pipelineOrchestrator.py --side-tasks) --")
	rc, _, err := runproc.Run(ctx, p.cfg.SideTaskTimeout,
		[]string{"IMPORTWRITE_URL=" + p.cfg.ImportWriteURL},
		"python3", filepath.Join(p.cfg.RepoRoot, "scripts", "pipelineOrchestrator.py"), "--side-tasks")
	if err != nil || rc != 0 {
		fmt.Printf("side tasks failed (rc=%d): %v\n", rc, err)
	}
}

// RunLoop runs the pipeline in a loop until ctx is done.
func (p *Pipeline) RunLoop(ctx context.Context) {
	for {
		p.RunOnce(ctx)
		select {
		case <-ctx.Done():
			return
		case <-time.After(p.cfg.PollInterval):
		}
	}
}

// Store returns the queue store for dashboard access.
// Config returns the pipeline's resolved configuration.
func (p *Pipeline) Config() Config { return p.cfg }

func (p *Pipeline) Store() *queue.Store {
	return p.store
}

// Stop stops the pipeline.
func (p *Pipeline) Stop() {
	close(p.stop)
}

// ncLicence matches sourceQueue/importQueueDriver's licence gate: "nc" as
// its own word once spaces and hyphens are normalised ("CC BY-NC 4.0").
var ncLicence = regexp.MustCompile(`\bnc\b`)
var licenceSep = regexp.MustCompile(`[\s-]+`)

func (p *Pipeline) processOne(ctx context.Context, key string, entry *queue.Entry) {
	fmt.Printf("== %s — %s\n", key, entry.Title)

	licence := licenceSep.ReplaceAllString(strings.ToLower(entry.Licence), " ")
	if ncLicence.MatchString(licence) {
		fmt.Printf("  %s: blocked — NC licence\n", key)
		p.store.SetStageReason(key, entry, queue.StageBlocked,
			fmt.Sprintf("CC BY-NC licence (%s) -- needs a policy decision, see docs/dataset-inbox.md", entry.Licence))
		return
	}

	if entry.ArchivePath == "" {
		entry.ArchivePath = download.ArchivePath(p.cfg.SourcesRoot, key)
	}

	// A queued source whose transform output is already on disk only
	// needs the apply step.
	if entry.Stage == queue.StageQueued && hasTransformOutput(p.cfg.SourcesRoot, key) {
		p.applyOne(ctx, key, entry)
		return
	}

	// Stage 0: download archive if not present.
	if !fileExists(entry.ArchivePath) && p.cfg.NoDownload {
		fmt.Printf("  %s: no archive at %s and downloads are off -- waiting\n", key, entry.ArchivePath)
		return
	}
	if !fileExists(entry.ArchivePath) {
		fmt.Printf("  %s: downloading archive\n", key)
		result, err := p.dl.Run(ctx, key)
		switch {
		case result != nil && result.RC == 3:
			p.store.SetStageReason(key, entry, queue.StageBlocked, "archive missing and key is not a ChecklistBank dataset")
			return
		case result != nil && result.RC == 4:
			p.store.SetStageReason(key, entry, queue.StageBlocked, fmt.Sprintf("download is not an archive: %v", err))
			return
		case err != nil:
			fmt.Printf("  %s: download FAILED: %v -- leaving at %s\n", key, err, entry.Stage)
			return
		}
		entry.ArchivePath = download.ArchivePath(p.cfg.SourcesRoot, key)
		if entry.Stage == queue.StageCandidate {
			p.store.SetStage(key, entry, queue.StageDownloaded)
		}
	}

	// Stage 1: transform.
	fmt.Printf("  %s: transforming\n", key)
	p.store.SetStage(key, entry, queue.StageTransforming)
	result, err := p.tr.Run(ctx, entry.ArchivePath, key, entry.KingdomOverride)
	if errors.Is(err, runproc.ErrTimeout) {
		p.store.SetStageReason(key, entry, queue.StageError,
			fmt.Sprintf("transform timed out after %s", p.cfg.TransformTimeout))
		return
	}
	if err != nil {
		p.store.SetStageReason(key, entry, queue.StageError, fmt.Sprintf("transform: %v", err))
		return
	}

	switch result.RC {
	case 0:
	case 3:
		p.store.SetStageReason(key, entry, queue.StageBlocked, "txtree format — needs scripts/txtree.py path, see docs/import.md")
		return
	case 4:
		p.store.SetStageReason(key, entry, queue.StageBlocked, "unsupported archive format (no .txtree, no DwCA/ColDP table)")
		return
	default:
		fmt.Printf("  %s: transform FAILED (rc=%d), leaving at downloaded\n", key, result.RC)
		p.store.SetStageReason(key, entry, queue.StageDownloaded, fmt.Sprintf("transform failed (rc=%d)", result.RC))
		return
	}

	if strings.Contains(result.Output, "nothing to do") {
		fmt.Printf("  %s: applied — nothing to do (all already held)\n", key)
		p.store.SetStageWithStats(key, entry, queue.StageApplied, 0, 0, 0, 0)
		return
	}

	p.store.SetTriaged(key, entry, parseTriaged(result.Output))
	p.store.SetStage(key, entry, queue.StageQueued)
	p.applyOne(ctx, key, entry)
}

func (p *Pipeline) applyOne(ctx context.Context, key string, entry *queue.Entry) {
	fmt.Printf("  %s: applying\n", key)
	p.store.SetStage(key, entry, queue.StageApplying)

	res, err := p.ap.Run(ctx, key, p.cfg.ImportWriteURL)
	if errors.Is(err, runproc.ErrTimeout) {
		p.store.SetStageReason(key, entry, queue.StageError,
			fmt.Sprintf("apply timed out after %s", p.cfg.ApplyTimeout))
		return
	}
	if err != nil {
		p.store.SetStageReason(key, entry, queue.StageError, fmt.Sprintf("apply: %v", err))
		return
	}
	if res.RC != 0 {
		fmt.Printf("  %s: apply FAILED (rc=%d), marking error\n", key, res.RC)
		p.store.SetStageReason(key, entry, queue.StageError, fmt.Sprintf("apply failed (rc=%d)", res.RC))
		return
	}

	added, merged, cross, families := parseApplied(res.Output)
	fmt.Printf("  %s: applied — +%d added, %d merged, %d cross-family, %d families\n",
		key, added, merged, cross, families)
	p.store.SetStageWithStats(key, entry, queue.StageApplied, added, merged, cross, families)
}

// The patterns below are the ones importQueueDriver.py parses, against the
// lines importColChecklist.route_species() and importTransformed.py print.
var (
	reOffered = regexp.MustCompile(`offered:\s*([\d,]+)`)
	reHeld    = regexp.MustCompile(`already held \(skipped\):\s*([\d,]+)`)
	reStaged  = regexp.MustCompile(`staged:\s*([\d,]+)`)
	reRefused = regexp.MustCompile(`REFUSED \(would need a new family\):\s*([\d,]+)`)
	reIW      = regexp.MustCompile(`importwrite:\s*(\d+)\s+added,\s*(\d+)\s+merged`)
	reCross   = regexp.MustCompile(`\(\s*(\d+)\s+already existed`)
	reFlushed = regexp.MustCompile(`flushed\s+(\d+)\s+famil(?:y|ies)`)
)

func num(re *regexp.Regexp, s string, group int) *int {
	m := re.FindStringSubmatch(s)
	if m == nil {
		return nil
	}
	n, err := strconv.Atoi(strings.ReplaceAll(m[group], ",", ""))
	if err != nil {
		return nil
	}
	return &n
}

func parseTriaged(out string) *queue.TriagedStats {
	t := &queue.TriagedStats{
		Offered:     num(reOffered, out, 1),
		AlreadyHeld: num(reHeld, out, 1),
		Staged:      num(reStaged, out, 1),
		Refused:     num(reRefused, out, 1),
	}
	if t.Offered != nil && t.Refused != nil && *t.Offered > 0 {
		r := float64(int(float64(*t.Refused)/float64(*t.Offered)*10000+0.5)) / 10000
		t.RefusalRate = &r
	}
	return t
}

func parseApplied(out string) (added, merged, cross, families int) {
	if v := num(reIW, out, 1); v != nil {
		added = *v
	}
	if v := num(reIW, out, 2); v != nil {
		merged = *v
	}
	if v := num(reCross, out, 1); v != nil {
		cross = *v
	}
	if v := num(reFlushed, out, 1); v != nil {
		families = *v
	}
	return
}

func hasTransformOutput(sourcesRoot, key string) bool {
	info, err := os.Stat(filepath.Join(sourcesRoot, "work", key, "transformed.jsonl"))
	return err == nil && info.Size() > 0
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
