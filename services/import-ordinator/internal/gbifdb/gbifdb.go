// Package gbifdb lists GBIF's checklist datasets against the import
// pipeline, so every one of them can be seen to carry a decision.
//
// GBIF keys are UUIDs and the pipeline is keyed by ChecklistBank dataset
// (checklistbank-<key>); <sources>/gbif-dataset-map.json, written by
// scripts/gbifDatasetMap.py, links the two. A dataset's status is, in
// order: its pipeline queue stage, else its manifest status (matched by
// ChecklistBank key, DOI or title -- the pipeline often holds the same
// data under a different ChecklistBank key than GBIF's mirror), else the
// decision recorded from the dashboard (skip / add), else "undecided".
//
// Decisions are kept in the repo, data/gbif-dataset-decisions.json, next to
// the queue they feed -- not on the sources volume -- so they are
// versioned like every other pipeline decision.
package gbifdb

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"systema-naturae/import-ordinator/internal/queue"
	"systema-naturae/import-ordinator/internal/runproc"
)

// Dataset is one GBIF checklist dataset with its pipeline-aligned status.
type Dataset struct {
	Key             string `json:"key"` // GBIF dataset UUID
	ClbKey          int    `json:"clbKey,omitempty"`
	MatchedBy       string `json:"matchedBy,omitempty"` // gbifKey / doi / title
	Title           string `json:"title"`
	Type            string `json:"type"`
	Licence         string `json:"licence"` // short form: "cc by", "cc0", "cc by-nc", ...
	NameUsagesCount int    `json:"nameUsagesCount"`
	DOI             string `json:"doi,omitempty"`
	Country         string `json:"publishingCountry,omitempty"`

	// Status is the pipeline stage, manifest status, "skipped", "added" or
	// "undecided"; StatusFrom says which of pipeline/manifest/decision set it.
	Status      string `json:"status"`
	StatusFrom  string `json:"statusFrom,omitempty"`
	PipelineKey string `json:"pipelineKey,omitempty"` // queue key or manifest slug
	Reason      string `json:"reason,omitempty"`
	LastEventAt string `json:"lastEventAt,omitempty"`
}

// Decision is a dashboard decision on one GBIF dataset.
type Decision struct {
	Decision string `json:"decision"` // "skip" or "add"
	At       string `json:"at"`
	ClbKey   int    `json:"clbKey,omitempty"`
	Title    string `json:"title,omitempty"`
}

var (
	mu            sync.Mutex
	datasets      []Dataset
	clbMap        map[string]mapRow
	decisions     map[string]Decision
	decisionsPath string
	manifestPath  string
	repoRoot      string
)

type mapRow struct {
	Clb int    `json:"clb"`
	By  string `json:"by"`
}

// Init loads the GBIF dataset list (top N by name usages), the
// GBIF->ChecklistBank map and the recorded decisions.
func Init(sourcesRoot, repo string, topN int) error {
	mu.Lock()
	defer mu.Unlock()
	repoRoot = repo
	manifestPath = filepath.Join(sourcesRoot, "manifest.json")
	decisionsPath = filepath.Join(repo, "data", "gbif-dataset-decisions.json")

	if err := loadTSV(filepath.Join(sourcesRoot, "gbif-datasets.tsv"), topN); err != nil {
		return err
	}
	clbMap = map[string]mapRow{}
	if raw, err := os.ReadFile(filepath.Join(sourcesRoot, "gbif-dataset-map.json")); err == nil {
		json.Unmarshal(raw, &clbMap)
	}
	for i := range datasets {
		if m, ok := clbMap[datasets[i].Key]; ok {
			datasets[i].ClbKey, datasets[i].MatchedBy = m.Clb, m.By
		}
	}
	return loadDecisions(filepath.Join(sourcesRoot, "skip-decisions.json"))
}

func loadTSV(path string, topN int) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read gbif-datasets.tsv: %w", err)
	}
	lines := strings.Split(string(data), "\n")
	if len(lines) < 2 {
		return fmt.Errorf("gbif-datasets.tsv has no data rows")
	}
	col := map[string]int{}
	for i, h := range strings.Split(lines[0], "\t") {
		col[strings.TrimSpace(h)] = i
	}
	field := func(f []string, name string) string {
		if i, ok := col[name]; ok && i < len(f) {
			return strings.TrimSpace(f[i])
		}
		return ""
	}
	datasets = datasets[:0]
	for _, line := range lines[1:] {
		if strings.TrimSpace(line) == "" {
			continue
		}
		f := strings.Split(line, "\t")
		d := Dataset{
			Key:     field(f, "key"),
			Title:   field(f, "title"),
			Type:    field(f, "type"),
			Licence: shortLicence(field(f, "license")),
		}
		d.NameUsagesCount, _ = strconv.Atoi(field(f, "nameUsagesCount"))
		// Rows are ragged (some carry an empty column before the DOI), so
		// take the DOI from wherever it is and the country from the end.
		for _, v := range f {
			if v = strings.TrimSpace(v); strings.HasPrefix(v, "10.") {
				d.DOI = v
			}
		}
		if last := strings.TrimSpace(f[len(f)-1]); len(last) == 2 {
			d.Country = last
		}
		if d.Key != "" {
			datasets = append(datasets, d)
		}
	}
	sort.SliceStable(datasets, func(i, j int) bool {
		return datasets[i].NameUsagesCount > datasets[j].NameUsagesCount
	})
	if len(datasets) > topN {
		datasets = datasets[:topN]
	}
	return nil
}

// shortLicence turns GBIF's licence URL into the short form the source
// queue uses ("cc by", "cc0", "cc by-nc"), which its NC gate matches on.
func shortLicence(url string) string {
	u := strings.ToLower(url)
	switch {
	case strings.Contains(u, "publicdomain/zero"):
		return "cc0"
	case strings.Contains(u, "licenses/by-nc"):
		return "cc by-nc"
	case strings.Contains(u, "licenses/by"):
		return "cc by"
	case u == "":
		return ""
	default:
		return url
	}
}

func loadDecisions(legacyPath string) error {
	decisions = map[string]Decision{}
	if raw, err := os.ReadFile(decisionsPath); err == nil {
		if err := json.Unmarshal(raw, &decisions); err != nil {
			return fmt.Errorf("parse %s: %w", decisionsPath, err)
		}
		return nil
	}
	// One-time migration from the sources-volume file the first version of
	// this tab wrote ({"checklistbank-<uuid>": "skip"|"use"}).
	raw, err := os.ReadFile(legacyPath)
	if err != nil {
		return nil
	}
	var legacy map[string]string
	if json.Unmarshal(raw, &legacy) != nil {
		return nil
	}
	now := time.Now().UTC().Format(time.RFC3339)
	for k, v := range legacy {
		uuid := strings.TrimPrefix(k, "checklistbank-")
		dec := "skip"
		if v == "use" {
			dec = "add"
		}
		decisions[uuid] = Decision{Decision: dec, At: now, ClbKey: clbMap[uuid].Clb}
	}
	return saveDecisions()
}

func saveDecisions() error {
	data, err := json.MarshalIndent(decisions, "", " ")
	if err != nil {
		return err
	}
	tmp := decisionsPath + ".tmp"
	if err := os.WriteFile(tmp, append(data, '\n'), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, decisionsPath)
}

var (
	reClbURL = regexp.MustCompile(`checklistbank\.org/dataset/(\d+)`)
	reDOI    = regexp.MustCompile(`10\.\d{4,9}/[^\s;,]+`)
	reNorm   = regexp.MustCompile(`[^a-z0-9]+`)
)

func norm(s string) string { return reNorm.ReplaceAllString(strings.ToLower(s), "") }

type manifestHit struct{ slug, status string }

// manifestIndex reads the sources manifest (small; re-read per request so
// a status change there shows without a restart).
func manifestIndex() (byClb map[int]manifestHit, byDOI, byTitle map[string]manifestHit) {
	byClb, byDOI, byTitle = map[int]manifestHit{}, map[string]manifestHit{}, map[string]manifestHit{}
	raw, err := os.ReadFile(manifestPath)
	if err != nil {
		return
	}
	var doc struct {
		Sources map[string]struct {
			Title, Identifier, URL, Status string
		} `json:"sources"`
	}
	if json.Unmarshal(raw, &doc) != nil {
		return
	}
	for slug, s := range doc.Sources {
		h := manifestHit{slug, s.Status}
		if m := reClbURL.FindStringSubmatch(s.URL); m != nil {
			k, _ := strconv.Atoi(m[1])
			byClb[k] = h
		}
		if m := reDOI.FindString(s.Identifier); m != "" {
			byDOI[strings.ToLower(m)] = h
		}
		if t := norm(s.Title); t != "" {
			byTitle[t] = h
		}
	}
	return
}

// GetDatasets returns every listed dataset with its status, given the
// current queue.
func GetDatasets(entries map[string]*queue.Entry) []Dataset {
	mu.Lock()
	defer mu.Unlock()
	byClb, byDOI, byTitle := manifestIndex()
	out := make([]Dataset, len(datasets))
	copy(out, datasets)
	for i := range out {
		d := &out[i]
		if d.ClbKey != 0 {
			qk := fmt.Sprintf("checklistbank-%d", d.ClbKey)
			if e, ok := entries[qk]; ok {
				d.Status, d.StatusFrom, d.PipelineKey, d.Reason = string(e.Stage), "pipeline", qk, e.Reason
				if n := len(e.History); n > 0 {
					d.LastEventAt = e.History[n-1].At
				}
				continue
			}
		}
		if h, ok := byClb[d.ClbKey]; ok && d.ClbKey != 0 {
			d.Status, d.StatusFrom, d.PipelineKey = h.status, "manifest", h.slug
			continue
		}
		if h, ok := byDOI[strings.ToLower(d.DOI)]; ok && d.DOI != "" {
			d.Status, d.StatusFrom, d.PipelineKey = h.status, "manifest", h.slug
			continue
		}
		if h, ok := byTitle[norm(d.Title)]; ok {
			d.Status, d.StatusFrom, d.PipelineKey = h.status, "manifest", h.slug
			continue
		}
		if dec, ok := decisions[d.Key]; ok {
			d.Status, d.StatusFrom, d.LastEventAt = map[string]string{"skip": "skipped", "add": "added"}[dec.Decision], "decision", dec.At
			continue
		}
		d.Status = "undecided"
	}
	return out
}

func find(uuid string) (Dataset, bool) {
	for _, d := range datasets {
		if d.Key == uuid {
			return d, true
		}
	}
	return Dataset{}, false
}

// Skip records that the dataset was looked at and not wanted.
func Skip(uuid string) error {
	mu.Lock()
	defer mu.Unlock()
	d, ok := find(uuid)
	if !ok {
		return fmt.Errorf("unknown dataset %s", uuid)
	}
	decisions[uuid] = Decision{Decision: "skip", At: time.Now().UTC().Format(time.RFC3339), ClbKey: d.ClbKey, Title: d.Title}
	return saveDecisions()
}

// Clear removes a recorded decision (the queue entry an "add" created, if
// any, is left alone -- withdraw that through the queue).
func Clear(uuid string) error {
	mu.Lock()
	defer mu.Unlock()
	delete(decisions, uuid)
	return saveDecisions()
}

// Add puts the dataset's ChecklistBank copy on the pipeline queue as a
// candidate, through `sourceQueue.py add` so its manifest key/DOI/title
// overlap check still guards against re-adding something already held
// under another key. The ordinator downloads candidates on its next pass.
// Returns sourceQueue's output, which explains a refusal.
func Add(ctx context.Context, uuid string) (string, error) {
	mu.Lock()
	d, ok := find(uuid)
	mu.Unlock()
	if !ok {
		return "", fmt.Errorf("unknown dataset %s", uuid)
	}
	if d.ClbKey == 0 {
		return "", fmt.Errorf("no ChecklistBank copy of %q is known, so there is nothing the pipeline can download -- run scripts/gbifDatasetMap.py --refresh, or skip it", d.Title)
	}
	rc, out, err := runproc.Run(ctx, 2*time.Minute, nil, "python3",
		filepath.Join(repoRoot, "scripts", "sourceQueue.py"), "add",
		"--key", fmt.Sprintf("checklistbank-%d", d.ClbKey),
		"--title", d.Title, "--licence", d.Licence,
		"--size", strconv.Itoa(d.NameUsagesCount))
	if err != nil {
		return out, err
	}
	if rc != 0 {
		return out, fmt.Errorf("sourceQueue.py add refused (rc=%d)", rc)
	}
	mu.Lock()
	defer mu.Unlock()
	decisions[uuid] = Decision{Decision: "add", At: time.Now().UTC().Format(time.RFC3339), ClbKey: d.ClbKey, Title: d.Title}
	return out, saveDecisions()
}
