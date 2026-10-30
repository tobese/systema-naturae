package worker

import (
	"context"
	"path/filepath"
	"testing"

	"systema-naturae/import-ordinator/internal/queue"
)

// With downloads off, a candidate whose archive is not on this machine waits
// at its stage: no fetch, no transform, no stage change.
func TestProcessOne_NoDownloadWaits(t *testing.T) {
	repo := t.TempDir()
	p := NewPipeline(Config{
		RepoRoot:    repo,
		SourcesRoot: t.TempDir(),
		QueueDir:    filepath.Join(repo, "data", "source-queue-bv"),
		NoDownload:  true,
	})
	if got := p.Config().QueueDir; got != filepath.Join(repo, "data", "source-queue-bv") {
		t.Fatalf("QueueDir = %q", got)
	}
	key := "checklistbank-2169"
	if err := p.Store().Write(key, &queue.Entry{Key: key, Stage: queue.StageCandidate, Licence: "cc0"}); err != nil {
		t.Fatal(err)
	}
	entries, err := p.Store().Read()
	if err != nil {
		t.Fatal(err)
	}
	p.processOne(context.Background(), key, entries[key])

	after, _ := p.Store().Read()
	if after[key].Stage != queue.StageCandidate {
		t.Fatalf("stage = %s, want candidate", after[key].Stage)
	}
}
