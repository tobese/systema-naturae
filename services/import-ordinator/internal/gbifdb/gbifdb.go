// Package gbifdb loads and manages the GBIF datasets TSV file,
// providing sorted, filtered access with skip/use state tracking.
package gbifdb

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// Dataset is a GBIF dataset entry from the TSV file.
type Dataset struct {
	Key               string `json:"key"`
	Title             string `json:"title"`
	Type              string `json:"type"`
	Licence           string `json:"licence"`
	NameUsagesCount   int    `json:"nameUsagesCount"`
	DOI               string `json:"doi,omitempty"`
	PublishingCountry string `json:"publishingCountry,omitempty"`
	State             string `json:"state,omitempty"`    // queue state: candidate/downloaded/transforming/queued/applying/blocked/error
	Decision          string `json:"decision,omitempty"` // skip or use
}

var (
	datasets      []Dataset
	decisions     map[string]string // key -> "skip" or "use"
	decisionsPath string
	sourcesRoot   string
)

// Init loads the GBIF datasets TSV file, sorts by nameUsagesCount desc,
// takes top N, and loads skip/use decisions.
func Init(sourcesRootParam string, topN int) error {
	sourcesRoot = sourcesRootParam
	tsvPath := filepath.Join(sourcesRoot, "gbif-datasets.tsv")
	decisionsPath = filepath.Join(sourcesRoot, "skip-decisions.json")

	data, err := os.ReadFile(tsvPath)
	if err != nil {
		return fmt.Errorf("read gbif-datasets.tsv: %w", err)
	}

	lines := strings.Split(string(data), "\n")
	if len(lines) < 2 {
		return fmt.Errorf("gbif-datasets.tsv has no data rows")
	}

	// Parse header to find column indices
	header := strings.Split(lines[0], "\t")
	colIndex := make(map[string]int)
	for i, h := range header {
		colIndex[strings.TrimSpace(h)] = i
	}

	keyIdx := colIndex["key"]
	titleIdx := colIndex["title"]
	typeIdx := colIndex["type"]
	licenceIdx := colIndex["license"]
	nameUsagesIdx := colIndex["nameUsagesCount"]

	for i := 1; i < len(lines); i++ {
		line := strings.TrimSpace(lines[i])
		if line == "" {
			continue
		}
		fields := strings.Split(line, "\t")
		if len(fields) <= keyIdx {
			continue
		}

		d := Dataset{
			Key: strings.TrimSpace(fields[keyIdx]),
		}

		if titleIdx < len(fields) {
			d.Title = strings.TrimSpace(fields[titleIdx])
		}
		if typeIdx < len(fields) {
			d.Type = strings.TrimSpace(fields[typeIdx])
		}
		if licenceIdx < len(fields) {
			d.Licence = strings.TrimSpace(fields[licenceIdx])
		}
		if nameUsagesIdx < len(fields) {
			d.NameUsagesCount, _ = strconv.Atoi(strings.TrimSpace(fields[nameUsagesIdx]))
		}

		// Handle both 7-field and 8-field rows (some rows have an empty field
		// between nameUsagesCount and doi)
		var doiIdx, publishingCountryIdx int
		if len(fields) >= 8 && nameUsagesIdx+1 < len(fields) && fields[nameUsagesIdx+1] == "" {
			doiIdx = nameUsagesIdx + 2
			publishingCountryIdx = nameUsagesIdx + 3
		} else {
			doiIdx = nameUsagesIdx + 1
			publishingCountryIdx = nameUsagesIdx + 2
		}

		if doiIdx < len(fields) {
			d.DOI = strings.TrimSpace(fields[doiIdx])
		}
		if publishingCountryIdx < len(fields) {
			d.PublishingCountry = strings.TrimSpace(fields[publishingCountryIdx])
		}

		datasets = append(datasets, d)
	}

	// Sort by nameUsagesCount desc
	sort.Slice(datasets, func(i, j int) bool {
		return datasets[i].NameUsagesCount > datasets[j].NameUsagesCount
	})

	// Take top N
	if len(datasets) > topN {
		datasets = datasets[:topN]
	}

	// Load skip/use decisions
	if err := loadDecisions(); err != nil {
		return err
	}

	return nil
}

func loadDecisions() error {
	data, err := os.ReadFile(decisionsPath)
	if err != nil {
		if os.IsNotExist(err) {
			decisions = make(map[string]string)
			return nil
		}
		return err
	}
	return json.Unmarshal(data, &decisions)
}

func saveDecisions() error {
	data, err := json.MarshalIndent(decisions, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(decisionsPath, data, 0644)
}

// GetDatasets returns all datasets with their current state.
func GetDatasets() []Dataset {
	result := make([]Dataset, len(datasets))
	copy(result, datasets)
	for i := range result {
		if state, ok := decisions[result[i].Key]; ok {
			result[i].State = state
		}
		if decision, ok := decisions[result[i].Key]; ok {
			result[i].Decision = decision
		}
	}
	return result
}

// PipelineInfo holds the fields we copy from a pipeline queue entry
// when enriching a GBIF dataset that matches a locally held source.
type PipelineInfo struct {
	Key     string
	Licence string
	Stage   string
}

// EnrichWithPipelineState matches datasets to pipeline queue entries by title
// and copies the pipeline key, licence, and stage for locally held sources.
// pipelineEntries maps a source title to its pipeline info.
func EnrichWithPipelineState(datasets []Dataset, pipelineEntries map[string]PipelineInfo) []Dataset {
	result := make([]Dataset, len(datasets))
	copy(result, datasets)
	for i := range result {
		if info, ok := pipelineEntries[result[i].Title]; ok {
			result[i].Key = info.Key
			result[i].Licence = info.Licence
			result[i].State = info.Stage
		}
	}
	return result
}

// SetDecision sets the skip/use decision for a dataset.
func SetDecision(key, decision string) {
	decisions[key] = decision
	saveDecisions()
}

// GetState returns the queue stage for a dataset key.
func GetState(key string) string {
	return decisions[key]
}

// IsSkipped returns true if the dataset is marked as skip.
func IsSkipped(key string) bool {
	return decisions[key] == "skip"
}

// IsUsed returns true if the dataset is marked as use.
func IsUsed(key string) bool {
	return decisions[key] == "use"
}

// ShortKey returns a shortened key for display (first 8 chars).
func ShortKey(key string) string {
	if len(key) > 8 {
		return key[:8]
	}
	return key
}
