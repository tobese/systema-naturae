package main

import (
	"fmt"
	"log"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// store is the registry of families currently loaded in memory. It is the
// only writer to each family's JSON file: every POST for a given slug goes
// through the same *familyState, so concurrent importers are serialized
// instead of racing to edit (and git-merge) the file independently.
type store struct {
	root      string
	gitCommit bool
	idleEvict time.Duration
	mu        sync.Mutex
	families  map[string]*familyState
}

func newStore(root string, gitCommit bool, idleEvict time.Duration) *store {
	return &store{
		root:      root,
		gitCommit: gitCommit,
		idleEvict: idleEvict,
		families:  map[string]*familyState{},
	}
}

func (s *store) get(loc familyLocation) (*familyState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if fs, ok := s.families[loc.Slug]; ok {
		return fs, nil
	}
	fs, err := loadFamily(s.root, loc)
	if err != nil {
		return nil, err
	}
	s.families[loc.Slug] = fs
	return fs, nil
}

// flushLoop periodically flushes every dirty family to disk and, if
// gitCommit is enabled, commits the result. This is the durable boundary:
// in-memory state is a staging buffer in front of the file on disk, not a
// second source of truth, so it should be flushed eagerly rather than held
// for a big batch.
func (s *store) flushLoop(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for range ticker.C {
		s.flushAll()
		s.evictIdle()
	}
}

func (s *store) flushAll() {
	s.mu.Lock()
	snapshot := make([]*familyState, 0, len(s.families))
	for _, fs := range s.families {
		snapshot = append(snapshot, fs)
	}
	s.mu.Unlock()

	for _, fs := range snapshot {
		wrote, err := fs.flush()
		if err != nil {
			log.Printf("flush %s: %v", fs.slug, err)
			continue
		}
		if wrote {
			log.Printf("flushed %s -> %s", fs.slug, fs.file)
			if s.gitCommit {
				if err := commitFamily(s.root, fs.slug, fs.file); err != nil {
					log.Printf("git commit %s: %v", fs.slug, err)
				}
			}
		}
	}
}

// evictIdle drops families that are clean (already flushed) and haven't
// been written to in idleEvict, bounding memory to what's actively
// importing rather than the whole tree.
func (s *store) evictIdle() {
	if s.idleEvict <= 0 {
		return
	}
	cutoff := time.Now().Add(-s.idleEvict)
	s.mu.Lock()
	defer s.mu.Unlock()
	for slug, fs := range s.families {
		fs.mu.Lock()
		idle := !fs.dirty && fs.lastWrite.Before(cutoff) && !fs.lastWrite.IsZero()
		fs.mu.Unlock()
		if idle {
			delete(s.families, slug)
			log.Printf("evicted idle family %s", slug)
		}
	}
}

func commitFamily(root, slug, file string) error {
	rel, err := filepath.Rel(root, file)
	if err != nil {
		return err
	}
	if out, err := exec.Command("git", "-C", root, "add", rel).CombinedOutput(); err != nil {
		return fmt.Errorf("git add: %w: %s", err, out)
	}
	msg := fmt.Sprintf("importwrite: update %s", slug)
	out, err := exec.Command("git", "-C", root, "commit", "-m", msg, "--", rel).CombinedOutput()
	if err != nil {
		// "nothing to commit" is not an error worth surfacing (can happen if
		// a write round-tripped to the same bytes already on disk).
		text := string(out)
		if strings.Contains(text, "nothing to commit") || strings.Contains(text, "nothing added") {
			return nil
		}
		return fmt.Errorf("git commit: %w: %s", err, out)
	}
	return nil
}
