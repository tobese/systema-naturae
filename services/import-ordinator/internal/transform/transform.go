// Package transform runs transformColChecklist.py as a subprocess with
// timeout and progress tracking.
package transform

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"systema-naturae/import-ordinator/internal/runproc"
)

// Result is the result of a transform run.
type Result struct {
	RC     int
	Output string
}

// Progress is the transform progress sidecar.
type Progress struct {
	WorkSlug    string  `json:"work_slug"`
	TotalStaged *int    `json:"total_staged,omitempty"`
	Written     *int    `json:"written,omitempty"`
	UpdatedAt   float64 `json:"updated_at,omitempty"`
	Complete    bool    `json:"complete,omitempty"`
	Phase       string  `json:"phase,omitempty"`
}

// Runner runs transformColChecklist.py as a subprocess.
type Runner struct {
	ScriptDir   string
	SourcesRoot string
	Timeout     time.Duration
}

// Run runs transformColChecklist.py for the given archive and work slug.
// kingdom, when set, is the queue entry's kingdomOverride: a single-kingdom
// source whose rows carry no kingdom (ICTV left 2,836 species unresolved
// without it, 2026-10-30).
func (r *Runner) Run(ctx context.Context, archive, workSlug, kingdom string) (*Result, error) {
	progressPath := filepath.Join(r.SourcesRoot, "work", workSlug, "transform.progress.json")
	os.MkdirAll(filepath.Dir(progressPath), 0755)
	writeProgress(progressPath, workSlug, nil, nil, false, "routing")

	args := []string{filepath.Join(r.ScriptDir, "transformColChecklist.py"), archive, workSlug, "--apply"}
	if kingdom != "" {
		args = append(args, "--kingdom", kingdom)
	}
	rc, out, err := runproc.Run(ctx, r.Timeout, []string{"TQDM_DISABLE=1"}, "python3", args...)
	if err != nil {
		return &Result{RC: rc, Output: out}, fmt.Errorf("transform: %w", err)
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
func writeProgress(progressPath, workSlug string, totalStaged, written *int, complete bool, phase string) {
	p := Progress{
		WorkSlug:    workSlug,
		TotalStaged: totalStaged,
		Written:     written,
		UpdatedAt:   float64(time.Now().Unix()),
		Complete:    complete,
		Phase:       phase,
	}
	data, _ := json.Marshal(p)
	os.WriteFile(progressPath, data, 0644)
}
