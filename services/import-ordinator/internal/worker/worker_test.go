package worker

import (
	"context"
	"strings"
	"testing"

	"systema-naturae/import-ordinator/internal/queue"
)

func TestParseTriaged(t *testing.T) {
	out := "  accepted species/subspecies offered: 4,305\n\n  already held (skipped): 1,298\n  staged:              2,000\n  REFUSED (would need a new family): 1,007 (23.4%)\n"
	tr := parseTriaged(out)
	if tr.Offered == nil || *tr.Offered != 4305 || *tr.AlreadyHeld != 1298 || *tr.Staged != 2000 || *tr.Refused != 1007 {
		t.Fatalf("bad parse: %+v", tr)
	}
	if tr.RefusalRate == nil || *tr.RefusalRate != 0.2339 {
		t.Fatalf("bad refusal rate: %v", *tr.RefusalRate)
	}
	if parseTriaged("nothing").Offered != nil {
		t.Fatal("missing number must stay nil, not zero")
	}
}

func TestParseApplied(t *testing.T) {
	out := "  importwrite: 179 added, 1419 merged (2 already existed in a different family)\n  flushed 515 families\n"
	a, m, c, f := parseApplied(out)
	if a != 179 || m != 1419 || c != 2 || f != 515 {
		t.Fatalf("got %d %d %d %d", a, m, c, f)
	}
}

func TestNCLicence(t *testing.T) {
	for lic, want := range map[string]bool{"CC BY-NC 4.0": true, "cc by nc": true, "cc by": false, "cc0": false, "unknown licence": false} {
		got := ncLicence.MatchString(licenceSep.ReplaceAllString(strings.ToLower(lic), " "))
		if got != want {
			t.Errorf("%q: got %v want %v", lic, got, want)
		}
	}
}

func TestFailureReason(t *testing.T) {
	out := "  loading\nTraceback (most recent call last):\n  File \"x.py\"\nKeyError: \"no column for ['rank']\"\n\n"
	if got, want := failureReason("transform", 1, out), "transform failed (rc=1): KeyError: \"no column for ['rank']\""; got != want {
		t.Errorf("got %q, want %q", got, want)
	}
	if got, want := failureReason("apply", 2, ""), "apply failed (rc=2)"; got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

func TestStopStartsNoFurtherSource(t *testing.T) {
	dir := t.TempDir()
	p := NewPipeline(Config{RepoRoot: dir, QueueDir: dir, NoDownload: true, NoSideTasks: true})
	if err := p.store.Write("checklistbank-1", &queue.Entry{Key: "checklistbank-1", Stage: queue.StageDownloaded}); err != nil {
		t.Fatal(err)
	}
	p.Stop()
	p.Stop() // idempotent: a second signal must not panic
	p.drain(context.Background())
	e, err := p.store.ReadOne("checklistbank-1")
	if err != nil {
		t.Fatal(err)
	}
	if e.Stage != queue.StageDownloaded {
		t.Fatalf("a stopping pipeline touched a source: stage %q", e.Stage)
	}
}

func TestStopDuringASourceStartsNoNext(t *testing.T) {
	// One worker busy on a source, a stop requested while it runs: the next
	// key must not start once the slot frees. The slot is held here by hand
	// to stand in for the busy worker.
	dir := t.TempDir()
	p := NewPipeline(Config{RepoRoot: dir, QueueDir: dir, NoDownload: true, NoSideTasks: true, Workers: 1})
	for _, k := range []string{"checklistbank-1", "checklistbank-2"} {
		if err := p.store.Write(k, &queue.Entry{Key: k, Stage: queue.StageDownloaded}); err != nil {
			t.Fatal(err)
		}
	}
	// Mark the first as already taken so drain's first candidate is the
	// second, then stop before drain gets to it.
	if err := p.store.Write("checklistbank-1", &queue.Entry{Key: "checklistbank-1", Stage: queue.StageApplied}); err != nil {
		t.Fatal(err)
	}
	p.Stop()
	p.drain(context.Background())
	e, _ := p.store.ReadOne("checklistbank-2")
	if e.Stage != queue.StageDownloaded {
		t.Fatalf("started a source after stop: %q", e.Stage)
	}
}

func TestTriagedIsLeftForAHuman(t *testing.T) {
	dir := t.TempDir()
	p := NewPipeline(Config{RepoRoot: dir, QueueDir: dir, NoDownload: true, NoSideTasks: true})
	if err := p.store.Write("checklistbank-1", &queue.Entry{Key: "checklistbank-1", Stage: queue.StageTriaged}); err != nil {
		t.Fatal(err)
	}
	p.drain(context.Background())
	e, _ := p.store.ReadOne("checklistbank-1")
	if e.Stage != queue.StageTriaged {
		t.Fatalf("a triaged source was moved to %q", e.Stage)
	}
}
