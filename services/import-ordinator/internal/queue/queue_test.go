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
