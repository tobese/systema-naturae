// Package dashboard serves the import pipeline web UI.
package dashboard

import (
	_ "embed"
	"encoding/json"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	"systema-naturae/import-ordinator/internal/gbifdb"
	"systema-naturae/import-ordinator/internal/queue"
)

//go:embed dashboard.html
var dashboardHTML string

// Dashboard serves the import pipeline web UI.
type Dashboard struct {
	store *queue.Store

	// HTMLPath, when set, is read on every request, so editing the page
	// needs only a browser reload. If it can't be read, the embedded copy
	// is served instead.
	HTMLPath string
}

// NewDashboard creates a new dashboard.
func NewDashboard(store *queue.Store) *Dashboard {
	return &Dashboard{store: store}
}

// Handler returns an http.Handler for the dashboard.
func (d *Dashboard) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/", d.HandleIndex)
	mux.HandleFunc("/queue", d.HandleQueue)
	mux.HandleFunc("/source/", d.HandleSource)
	mux.HandleFunc("/stuck", d.HandleStuck)
	mux.HandleFunc("/gbif", d.HandleGBIF)
	mux.HandleFunc("/gbif/", d.HandleGBIFToggle)
	return mux
}

// HandleIndex serves the dashboard HTML page.
func (d *Dashboard) HandleIndex(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if d.HTMLPath != "" {
		if page, err := os.ReadFile(d.HTMLPath); err == nil {
			w.Header().Set("Cache-Control", "no-store")
			w.Write(page)
			return
		}
	}
	w.Write([]byte(dashboardHTML))
}

// HandleQueue returns JSON of all queue entries.
func (d *Dashboard) HandleQueue(w http.ResponseWriter, r *http.Request) {
	entries, err := d.store.Read()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	type queueEntry struct {
		Key             string               `json:"key"`
		Title           string               `json:"title"`
		Stage           string               `json:"stage"`
		Licence         string               `json:"licence,omitempty"`
		Size            *int                 `json:"size,omitempty"`
		Added           *int                 `json:"added,omitempty"`
		Merged          *int                 `json:"merged,omitempty"`
		Families        *int                 `json:"families,omitempty"`
		Refused         *int                 `json:"refused,omitempty"`
		RefusalRate     *float64             `json:"refusalRate,omitempty"`
		Offered         *int                 `json:"offered,omitempty"`
		Staged          *int                 `json:"staged,omitempty"`
		LastEventAt     string               `json:"lastEventAt,omitempty"`
		Reason          string               `json:"reason,omitempty"`
		ActivePID       int                  `json:"activePid,omitempty"`
		ActiveStartedAt string               `json:"activeStartedAt,omitempty"`
		History         []queue.HistoryEntry `json:"history,omitempty"`
	}

	result := make([]queueEntry, 0, len(entries))
	for key, entry := range entries {
		qe := queueEntry{
			Key:             key,
			Title:           entry.Title,
			Stage:           string(entry.Stage),
			Licence:         entry.Licence,
			Size:            entry.Size,
			ActivePID:       entry.ActivePID,
			ActiveStartedAt: entry.ActiveStartedAt,
			History:         entry.History,
			Reason:          entry.Reason,
		}
		if n := len(entry.History); n > 0 {
			qe.LastEventAt = normalizeTime(entry.History[n-1].At)
		}
		if entry.Applied != nil {
			qe.Added = &entry.Applied.Added
			qe.Merged = &entry.Applied.Merged
			qe.Families = &entry.Applied.Families
		}
		if entry.Triaged != nil {
			qe.Refused = entry.Triaged.Refused
			qe.RefusalRate = entry.Triaged.RefusalRate
			qe.Offered = entry.Triaged.Offered
			qe.Staged = entry.Triaged.Staged
		}
		result = append(result, qe)
	}

	// Sort by stage (active first) then by key
	sort.Slice(result, func(i, j int) bool {
		stageOrder := map[string]int{
			"transforming": 0,
			"applying":     1,
			"triaging":     2,
			"triaged":      3,
			"queued":       4,
			"downloaded":   5,
			"candidate":    6,
			"applied":      7,
			"blocked":      8,
			"error":        9,
			"declined":     9,
		}
		oi, ok := stageOrder[result[i].Stage]
		if !ok {
			oi = 99
		}
		oj, ok := stageOrder[result[j].Stage]
		if !ok {
			oj = 99
		}
		if oi != oj {
			return oi < oj
		}
		return result[i].Key < result[j].Key
	})

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// HandleSource returns JSON for a single source.
func (d *Dashboard) HandleSource(w http.ResponseWriter, r *http.Request) {
	key := strings.TrimPrefix(r.URL.Path, "/source/")
	if key == "" || key == "source" {
		http.NotFound(w, r)
		return
	}

	entries, err := d.store.Read()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	entry, ok := entries[key]
	if !ok {
		http.NotFound(w, r)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(entry)
}

// HandleStuck returns JSON of sources stuck in active stages.
func (d *Dashboard) HandleStuck(w http.ResponseWriter, r *http.Request) {
	entries, err := d.store.Read()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	type stuckEntry struct {
		Key             string `json:"key"`
		Title           string `json:"title"`
		Stage           string `json:"stage"`
		ActivePID       int    `json:"activePid,omitempty"`
		ActiveStartedAt string `json:"activeStartedAt,omitempty"`
		ArchivePath     string `json:"archivePath,omitempty"`
		AgeInStage      string `json:"ageInStage,omitempty"`
	}

	var stuck []stuckEntry
	for key, entry := range entries {
		if !queue.IsActive(entry.Stage) {
			continue
		}
		se := stuckEntry{
			Key:             key,
			Title:           entry.Title,
			Stage:           string(entry.Stage),
			ActivePID:       entry.ActivePID,
			ActiveStartedAt: entry.ActiveStartedAt,
			ArchivePath:     entry.ArchivePath,
		}
		if entry.ActiveStartedAt != "" {
			if t, err := time.Parse(time.RFC3339, entry.ActiveStartedAt); err == nil {
				se.AgeInStage = time.Since(t).String()
			}
		}
		stuck = append(stuck, se)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stuck)
}

// HandleGBIF returns GBIF datasets sorted by nameUsagesCount desc, with state info.
func (d *Dashboard) HandleGBIF(w http.ResponseWriter, r *http.Request) {
	entries, err := d.store.Read()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	datasets := gbifdb.GetDatasets(entries)
	for i := range datasets {
		if datasets[i].LastEventAt != "" {
			datasets[i].LastEventAt = normalizeTime(datasets[i].LastEventAt)
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(datasets)
}

// HandleGBIFToggle records a decision on a GBIF dataset:
// POST /gbif/{uuid}/skip | add | clear. "add" queues the dataset's
// ChecklistBank copy as a pipeline candidate (see gbifdb.Add); a refusal
// from the manifest overlap check comes back as 409 with its explanation.
func (d *Dashboard) HandleGBIFToggle(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	parts := strings.SplitN(strings.TrimPrefix(r.URL.Path, "/gbif/"), "/", 2)
	if len(parts) != 2 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}
	key, action := parts[0], parts[1]

	var out string
	var err error
	switch action {
	case "skip":
		err = gbifdb.Skip(key)
	case "clear":
		err = gbifdb.Clear(key)
	case "add":
		out, err = gbifdb.Add(r.Context(), key)
	default:
		http.Error(w, "Invalid action", http.StatusBadRequest)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	if err != nil {
		w.WriteHeader(http.StatusConflict)
		json.NewEncoder(w).Encode(map[string]string{"error": err.Error(), "output": strings.TrimSpace(out)})
		return
	}
	json.NewEncoder(w).Encode(map[string]string{"key": key, "action": action, "output": strings.TrimSpace(out)})
}

// historyLayouts are the timestamp shapes found in queue history: Go's
// RFC3339, Python's isoformat() (microseconds, "+00:00"), sourceQueue's
// "+0100" form, and a few naive local stamps from older tools.
var historyLayouts = []string{
	time.RFC3339Nano,
	"2006-01-02T15:04:05.999999-07:00",
	"2006-01-02T15:04:05-0700",
	"2006-01-02T15:04:05.999999",
	"2006-01-02T15:04:05",
}

// normalizeTime renders any history timestamp as RFC3339 UTC, so the
// dashboard can sort and format one shape. Unparseable input is returned
// unchanged rather than dropped.
func normalizeTime(s string) string {
	for _, layout := range historyLayouts {
		if t, err := time.Parse(layout, s); err == nil {
			return t.UTC().Format(time.RFC3339)
		}
	}
	return s
}
