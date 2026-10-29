// Package dashboard serves the import pipeline web UI.
package dashboard

import (
	_ "embed"
	"encoding/json"
	"net/http"
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
		}
		if entry.Applied != nil {
			qe.Added = &entry.Applied.Added
			qe.Merged = &entry.Applied.Merged
			qe.Families = &entry.Applied.Families
		}
		if entry.Triaged != nil {
			qe.Refused = entry.Triaged.Refused
			qe.RefusalRate = entry.Triaged.RefusalRate
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
	datasets := gbifdb.GetDatasets()

	// Enrich with pipeline stage for locally held sources (matched by title).
	entries, err := d.store.Read()
	if err == nil {
		pipelineEntries := make(map[string]gbifdb.PipelineInfo, len(entries))
		for _, entry := range entries {
			pipelineEntries[entry.Title] = gbifdb.PipelineInfo{
				Key:     entry.Key,
				Licence: entry.Licence,
				Stage:   string(entry.Stage),
			}
		}
		datasets = gbifdb.EnrichWithPipelineState(datasets, pipelineEntries)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(datasets)
}

// HandleGBIFToggle sets skip/use decision for a GBIF dataset.
func (d *Dashboard) HandleGBIFToggle(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse key and action from path: /gbif/{key}/{action}
	path := strings.TrimPrefix(r.URL.Path, "/gbif/")
	parts := strings.SplitN(path, "/", 2)
	if len(parts) != 2 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}
	key := parts[0]
	action := parts[1]

	if action != "skip" && action != "use" {
		http.Error(w, "Invalid action", http.StatusBadRequest)
		return
	}

	gbifdb.SetDecision(key, action)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"key": key, "action": action})
}
