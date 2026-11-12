package queue

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestWriteKeepsUnknownFields(t *testing.T) {
	dir := t.TempDir()
	in := `{"key":"checklistbank-1","title":"t","stage":"downloaded","licence":"cc by","measured":{"species":12},"notes":"keep me"}`
	os.WriteFile(filepath.Join(dir, "checklistbank-1.json"), []byte(in), 0644)
	os.WriteFile(filepath.Join(dir, "wikidata-species.json"), []byte(`{"key":"wikidata-species","stage":"declined"}`), 0644)

	s := NewStore(dir)
	entries, err := s.Read()
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 2 {
		t.Fatalf("non-checklistbank keys must be read too, got %d entries", len(entries))
	}
	e := entries["checklistbank-1"]
	if err := s.SetStage("checklistbank-1", e, StageQueued); err != nil {
		t.Fatal(err)
	}
	data, _ := os.ReadFile(filepath.Join(dir, "checklistbank-1.json"))
	var out map[string]any
	json.Unmarshal(data, &out)
	if out["notes"] != "keep me" || out["measured"] == nil {
		t.Fatalf("unknown fields dropped: %s", data)
	}
	if out["stage"] != "queued" {
		t.Fatalf("stage not written: %s", data)
	}
	ev, _ := os.ReadFile(filepath.Join(filepath.Dir(dir), "pipeline-events.jsonl"))
	if len(ev) == 0 {
		t.Fatal("no pipeline event logged")
	}
}

func TestReadOneSeesAChangeMadeAfterRead(t *testing.T) {
	s := NewStore(t.TempDir())
	if err := s.Write("checklistbank-1", &Entry{Key: "checklistbank-1", Stage: StageDownloaded}); err != nil {
		t.Fatal(err)
	}
	snap, err := s.Read()
	if err != nil {
		t.Fatal(err)
	}
	// a human declines it while the pass is still working through others
	if err := s.Write("checklistbank-1", &Entry{Key: "checklistbank-1", Stage: StageDeclined}); err != nil {
		t.Fatal(err)
	}
	if snap["checklistbank-1"].Stage != StageDownloaded {
		t.Fatal("snapshot should still hold the old stage")
	}
	fresh, err := s.ReadOne("checklistbank-1")
	if err != nil {
		t.Fatal(err)
	}
	if fresh.Stage != StageDeclined || CanProcess(fresh.Stage) {
		t.Fatalf("ReadOne returned %q; a declined entry must not be processed", fresh.Stage)
	}
}

// A parked source is a human's "not now": the drain must never pick it up
// (COL26.10, 2026-11-01).
func TestParkedIsNeverProcessed(t *testing.T) {
	if CanProcess(StageParked) || IsActive(StageParked) {
		t.Fatal("parked must be neither processable nor active")
	}
	if !IsTerminal(StageParked) {
		t.Fatal("parked must count as a resting stage")
	}
}

// A legal list is held back for a later legal-status layer, never drained
// as a checklist (2026-11-12).
func TestLegalIsNeverProcessed(t *testing.T) {
	if CanProcess(StageLegal) || IsActive(StageLegal) {
		t.Fatal("legal must be neither processable nor active")
	}
	if !IsTerminal(StageLegal) {
		t.Fatal("legal must count as a resting stage")
	}
}
