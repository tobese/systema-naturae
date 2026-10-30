// Package queue reads and writes source queue entries from
// data/source-queue/<key>.json.
package queue

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// Stage is the import pipeline stage for a source.
type Stage string

const (
	StageCandidate    Stage = "candidate"
	StageDownloaded   Stage = "downloaded"
	StageTransforming Stage = "transforming"
	StageTriaging     Stage = "triaging"
	StageTriaged      Stage = "triaged"
	StageQueued       Stage = "queued"
	StageApplying     Stage = "applying"
	StageApplied      Stage = "applied"
	StageDeclined     Stage = "declined"
	StageBlocked      Stage = "blocked"
	StageNeedsRerun   Stage = "needs-rerun"
	StageError        Stage = "error"
)

// Entry is a source queue entry.
//
// Extra keeps every field this struct doesn't name (e.g. "measured",
// written by the Python tools), so a stage change here never drops data
// another writer put in the file.
type Entry struct {
	Key             string         `json:"key"`
	Title           string         `json:"title"`
	Stage           Stage          `json:"stage"`
	Licence         string         `json:"licence"`
	Size            *int           `json:"size,omitempty"`
	ArchivePath     string         `json:"archivePath,omitempty"`
	KingdomOverride string         `json:"kingdomOverride,omitempty"`
	Added           *int           `json:"added,omitempty"`
	Merged          *int           `json:"merged,omitempty"`
	Families        *int           `json:"families,omitempty"`
	CrossFamily     *int           `json:"crossFamily,omitempty"`
	Reason          string         `json:"reason,omitempty"`
	ActivePID       int            `json:"activePid,omitempty"`
	ActiveStartedAt string         `json:"activeStartedAt,omitempty"`
	Applied         *AppliedStats  `json:"applied,omitempty"`
	Triaged         *TriagedStats  `json:"triaged,omitempty"`
	History         []HistoryEntry `json:"history,omitempty"`

	Extra map[string]json.RawMessage `json:"-"`
}

type entryAlias Entry

// namedKeys are Entry's JSON tags; anything else in a file goes to Extra.
var namedKeys = []string{"key", "title", "stage", "licence", "size", "archivePath",
	"kingdomOverride", "added", "merged", "families", "crossFamily", "reason",
	"activePid", "activeStartedAt", "applied", "triaged", "history"}

// UnmarshalJSON decodes the named fields and keeps the rest in Extra.
func (e *Entry) UnmarshalJSON(data []byte) error {
	var a entryAlias
	if err := json.Unmarshal(data, &a); err != nil {
		return err
	}
	var all map[string]json.RawMessage
	if err := json.Unmarshal(data, &all); err != nil {
		return err
	}
	for _, k := range namedKeys {
		delete(all, k)
	}
	*e = Entry(a)
	if len(all) > 0 {
		e.Extra = all
	}
	return nil
}

// MarshalJSON encodes the named fields plus everything kept in Extra.
func (e Entry) MarshalJSON() ([]byte, error) {
	data, err := json.Marshal(entryAlias(e))
	if err != nil || len(e.Extra) == 0 {
		return data, err
	}
	var all map[string]json.RawMessage
	if err := json.Unmarshal(data, &all); err != nil {
		return nil, err
	}
	for k, v := range e.Extra {
		if _, named := all[k]; !named {
			all[k] = v
		}
	}
	return json.Marshal(all)
}

// AppliedStats holds the apply step results.
type AppliedStats struct {
	Added       int    `json:"added"`
	Merged      int    `json:"merged"`
	CrossFamily int    `json:"crossFamily"`
	Families    int    `json:"families"`
	At          string `json:"at"`
}

// TriagedStats holds the transform step results. Pointers so a number the
// transform didn't print is recorded as absent rather than as zero.
type TriagedStats struct {
	Offered        *int     `json:"offered"`
	AlreadyHeld    *int     `json:"alreadyHeld"`
	Staged         *int     `json:"staged"`
	Refused        *int     `json:"refused"`
	RefusalRate    *float64 `json:"refusalRate"`
	Families       int      `json:"families,omitempty"`
	MissedFamilies int      `json:"missedFamilies,omitempty"`
}

// HistoryEntry is a stage transition record.
type HistoryEntry struct {
	At    string `json:"at"`
	Stage Stage  `json:"stage"`
	Note  string `json:"note,omitempty"`
}

// Store reads and writes source queue entries.
type Store struct {
	dir string
	mu  sync.Mutex
}

// NewStore creates a new queue store.
func NewStore(dir string) *Store {
	return &Store{dir: dir}
}

// Read reads all queue entries. Every <key>.json is a source -- keys are
// not all ChecklistBank ones (sourceQueue.py accepts any slug).
func (s *Store) Read() (map[string]*Entry, error) {
	entries := make(map[string]*Entry)
	matches, err := filepath.Glob(filepath.Join(s.dir, "*.json"))
	if err != nil {
		return nil, fmt.Errorf("glob queue files: %w", err)
	}

	for _, path := range matches {
		key := strings.TrimSuffix(filepath.Base(path), ".json")
		data, err := os.ReadFile(path)
		if err != nil {
			return nil, fmt.Errorf("read %s: %w", path, err)
		}
		var entry Entry
		if err := json.Unmarshal(data, &entry); err != nil {
			return nil, fmt.Errorf("parse %s: %w", path, err)
		}
		entries[key] = &entry
	}
	return entries, nil
}

// Write writes a single queue entry atomically (temp file + rename), so a
// reader never sees a half-written file.
func (s *Store) Write(key string, entry *Entry) error {
	path := filepath.Join(s.dir, key+".json")
	data, err := json.MarshalIndent(entry, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal %s: %w", key, err)
	}
	data = append(data, '\n')
	if err := os.MkdirAll(s.dir, 0o755); err != nil {
		return fmt.Errorf("queue dir for %s: %w", key, err)
	}
	tmp, err := os.CreateTemp(s.dir, "."+key+".*.tmp")
	if err != nil {
		return fmt.Errorf("temp for %s: %w", key, err)
	}
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		os.Remove(tmp.Name())
		return fmt.Errorf("write %s: %w", path, err)
	}
	tmp.Close()
	if err := os.Rename(tmp.Name(), path); err != nil {
		os.Remove(tmp.Name())
		return fmt.Errorf("rename %s: %w", path, err)
	}
	return nil
}

// logEvent appends one line to data/pipeline-events.jsonl, the same log
// sourceQueue.log_event() writes, so the Python dashboard and history
// tooling see this daemon's transitions too.
func (s *Store) logEvent(key string, stage Stage, extra map[string]any) {
	ev := map[string]any{
		"at":     time.Now().Format("2006-01-02T15:04:05-0700"),
		"key":    key,
		"stage":  stage,
		"action": "ordinator",
	}
	for k, v := range extra {
		ev[k] = v
	}
	line, err := json.Marshal(ev)
	if err != nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	f, err := os.OpenFile(filepath.Join(filepath.Dir(s.dir), "pipeline-events.jsonl"),
		os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	f.Write(append(line, '\n'))
}

// SetStage updates the stage of a queue entry and appends to history.
func (s *Store) SetStage(key string, entry *Entry, stage Stage) error {
	return s.SetStageReason(key, entry, stage, "")
}

// SetStageReason is SetStage with a reason recorded on the entry and in
// the event log (blocked/error transitions need one to be actionable).
func (s *Store) SetStageReason(key string, entry *Entry, stage Stage, reason string) error {
	entry.Stage = stage
	if reason != "" {
		entry.Reason = reason
	}
	entry.History = append(entry.History, HistoryEntry{
		At:    time.Now().UTC().Format(time.RFC3339),
		Stage: stage,
	})
	extra := map[string]any{}
	if reason != "" {
		extra["reason"] = reason
	}
	s.logEvent(key, stage, extra)
	return s.Write(key, entry)
}

// SetTriaged records the transform's routing numbers and moves to triaged.
func (s *Store) SetTriaged(key string, entry *Entry, t *TriagedStats) error {
	entry.Triaged = t
	return s.SetStage(key, entry, StageTriaged)
}

// SetStageWithStats updates the stage and stats of a queue entry.
func (s *Store) SetStageWithStats(key string, entry *Entry, stage Stage, added, merged, crossFamily, families int) error {
	entry.Stage = stage
	entry.Applied = &AppliedStats{
		Added:       added,
		Merged:      merged,
		CrossFamily: crossFamily,
		Families:    families,
		At:          time.Now().UTC().Format(time.RFC3339),
	}
	entry.History = append(entry.History, HistoryEntry{
		At:    time.Now().UTC().Format(time.RFC3339),
		Stage: stage,
	})
	s.logEvent(key, stage, map[string]any{
		"added": added, "merged": merged, "crossFamily": crossFamily, "families": families,
	})
	return s.Write(key, entry)
}

// SortKeys returns keys sorted by name.
func SortKeys(entries map[string]*Entry) []string {
	keys := make([]string, 0, len(entries))
	for k := range entries {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// IsTerminal reports whether a stage is terminal.
func IsTerminal(stage Stage) bool {
	switch stage {
	case StageApplied, StageDeclined, StageBlocked, StageError:
		return true
	default:
		return false
	}
}

// IsActive reports whether a stage is active (currently being processed).
func IsActive(stage Stage) bool {
	switch stage {
	case StageTransforming, StageTriaging, StageTriaged, StageApplying:
		return true
	default:
		return false
	}
}

// CanProcess reports whether a stage can be processed by the pipeline.
func CanProcess(stage Stage) bool {
	switch stage {
	case StageCandidate, StageDownloaded, StageQueued:
		return true
	default:
		return false
	}
}

// IsRefusable reports whether a stage can be refused/reset.
func IsRefusable(stage Stage) bool {
	switch stage {
	case StageTransforming, StageApplying:
		return true
	default:
		return false
	}
}
