// Package download fetches ChecklistBank archives via HTTP directly, without
// shelling out to fetchBatch.sh.
package download

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Result is the result of a download run.
type Result struct {
	RC     int
	Output string
}

// Runner downloads ChecklistBank archives via HTTP directly.
type Runner struct {
	SourcesRoot string
	Timeout     time.Duration
	UserAgent   string
}

// DefaultUserAgent matches fetchBatch.sh, so ChecklistBank sees one client.
const DefaultUserAgent = "systema-naturae-triage/1.0 (+https://github.com/tobese/systema-naturae)"

// Run downloads the archive for the given queue key ("checklistbank-1059").
// ChecklistBank's API wants the bare dataset number, so the prefix is
// stripped for the URL but kept for the on-disk directory, matching
// fetchBatch.sh. RC 3 means the key isn't a ChecklistBank one (nothing to
// fetch), RC 4 means the response wasn't an archive.
func (r *Runner) Run(ctx context.Context, key string) (*Result, error) {
	datasetKey, ok := strings.CutPrefix(key, "checklistbank-")
	if !ok {
		return &Result{RC: 3}, nil
	}
	url := fmt.Sprintf("https://api.checklistbank.org/dataset/%s/archive.zip", datasetKey)
	archivePath := ArchivePath(r.SourcesRoot, key)
	partPath := archivePath + ".part"

	if fileExists(archivePath) {
		fmt.Printf("== %s already on disk\n", key)
		return &Result{RC: 0, Output: "already on disk"}, nil
	}
	if err := os.MkdirAll(filepath.Dir(archivePath), 0755); err != nil {
		return &Result{RC: 1}, fmt.Errorf("create archive dir: %w", err)
	}

	fmt.Printf("== %s fetching %s\n", key, url)
	if r.Timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, r.Timeout)
		defer cancel()
	}
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return &Result{RC: 1}, fmt.Errorf("create request: %w", err)
	}
	ua := r.UserAgent
	if ua == "" {
		ua = DefaultUserAgent
	}
	req.Header.Set("User-Agent", ua)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return &Result{RC: 1}, fmt.Errorf("download request failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 200))
		return &Result{RC: 1}, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	// Stream to .part, hashing as we go -- archives run to gigabytes, so
	// never hold one in memory.
	out, err := os.Create(partPath)
	if err != nil {
		return &Result{RC: 1}, fmt.Errorf("create part file: %w", err)
	}
	h := sha256.New()
	written, err := io.Copy(io.MultiWriter(out, h), resp.Body)
	out.Close()
	if err != nil {
		os.Remove(partPath)
		return &Result{RC: 1}, fmt.Errorf("write archive: %w", err)
	}

	magic := make([]byte, 2)
	if f, err := os.Open(partPath); err == nil {
		io.ReadFull(f, magic)
		f.Close()
	}
	if string(magic) != "PK" && string(magic) != "\x1f\x8b" {
		os.Remove(partPath)
		return &Result{RC: 4}, fmt.Errorf("not an archive (magic=%q)", magic)
	}
	if err := os.Rename(partPath, archivePath); err != nil {
		return &Result{RC: 1}, fmt.Errorf("move archive: %w", err)
	}

	// Also copy as <dataset>.zip alongside, like fetchBatch.sh.
	keyZip := filepath.Join(filepath.Dir(archivePath), datasetKey+".zip")
	if err := copyFile(archivePath, keyZip); err != nil {
		fmt.Printf("   warning: could not copy %s: %v\n", keyZip, err)
	}
	fmt.Printf("   ok %.1f MB sha256:%x\n", float64(written)/1048576, h.Sum(nil))
	return &Result{RC: 0}, nil
}

// ArchivePath returns the expected path for a checklistbank archive.
func ArchivePath(sourcesRoot, key string) string {
	return filepath.Join(sourcesRoot, "archives", key, "archive.zip")
}

// Exists reports whether the archive for a key exists on disk.
func Exists(sourcesRoot, key string) bool {
	return fileExists(ArchivePath(sourcesRoot, key))
}

// IsStale reports whether an archive file is stale (older than threshold).
func IsStale(path string, threshold time.Duration) (bool, error) {
	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, err
	}
	return time.Since(info.ModTime()) > threshold, nil
}

// fileExists reports whether a file exists.
func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// copyFile copies a file from src to dst.
func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}
