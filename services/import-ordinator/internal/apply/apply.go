// Package apply runs importTransformed.py as a subprocess with
// timeout and progress tracking.
package apply

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"systema-naturae/import-ordinator/internal/runproc"
)

// Result is the result of an apply run.
type Result struct {
	RC     int
	Output string
}

// Progress is the apply progress sidecar.
type Progress struct {
	WorkSlug        string  `json:"work_slug"`
	TotalFamilies   *int    `json:"total_families,omitempty"`
	FamiliesWritten *int    `json:"families_written,omitempty"`
	Added           *int    `json:"added,omitempty"`
	Merged          *int    `json:"merged,omitempty"`
	CrossFamily     *int    `json:"cross_family,omitempty"`
	UpdatedAt       float64 `json:"updated_at,omitempty"`
	Complete        bool    `json:"complete,omitempty"`
	Phase           string  `json:"phase,omitempty"`
}

// Runner runs importTransformed.py as a subprocess.
type Runner struct {
	ScriptDir   string
	SourcesRoot string
	Timeout     time.Duration
}

// Run runs importTransformed.py for the given work slug.
func (r *Runner) Run(ctx context.Context, workSlug, importWriteURL string) (*Result, error) {
	progressPath := filepath.Join(r.SourcesRoot, "work", workSlug, "import.progress.json")
	writeProgress(progressPath, workSlug, nil, nil, nil, nil, nil, false, "applying")

	rc, out, err := runproc.Run(ctx, r.Timeout,
		[]string{"TQDM_DISABLE=1", "IMPORTWRITE_URL=" + importWriteURL},
		"python3", filepath.Join(r.ScriptDir, "importTransformed.py"), workSlug)
	if err != nil {
		return &Result{RC: rc, Output: out}, fmt.Errorf("apply: %w", err)
	}
	return &Result{RC: rc, Output: out}, nil
}

// IsStale reports whether a progress file is stale (no update for threshold duration).
func IsStale(progressPath string, threshold time.Duration) (bool, error) {
	data, err := os.ReadFile(progressPath)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, err
	}
	var p Progress
	if err := json.Unmarshal(data, &p); err != nil {
		return false, err
	}
	if p.UpdatedAt == 0 {
		return false, nil
	}
	updated := time.Unix(int64(p.UpdatedAt), 0)
	return time.Since(updated) > threshold, nil
}

// writeProgress writes a progress sidecar file.
func writeProgress(progressPath, workSlug string, totalFamilies, familiesWritten, added, merged, crossFamily *int, complete bool, phase string) {
	p := Progress{
		WorkSlug:        workSlug,
		TotalFamilies:   totalFamilies,
		FamiliesWritten: familiesWritten,
		Added:           added,
		Merged:          merged,
		CrossFamily:     crossFamily,
		UpdatedAt:       float64(time.Now().Unix()),
		Complete:        complete,
		Phase:           phase,
	}
	data, _ := json.Marshal(p)
	os.WriteFile(progressPath, data, 0644)
}
