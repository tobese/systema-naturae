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
	index     *globalIndex
	registry  *familyRegistry
}

func newStore(root string, gitCommit bool, idleEvict time.Duration) *store {
	return &store{
		root:      root,
		gitCommit: gitCommit,
		idleEvict: idleEvict,
		families:  map[string]*familyState{},
		index:     newGlobalIndex(),
		registry:  newFamilyRegistry(),
	}
}

// get is keyed by slug alone, which is NOT globally unique -- 103 families
// in the real tree are all named "incertae-sedis", sharing a slug across
// different kingdoms/phyla. A second, differently-located family with the
// same slug would silently share this one's cache slot. Not fixed here:
// this service only ever creates/loads families through a single explicit
// importRequest (kingdom+phylum+class+order+slug), never discovers them by
// slug search the way the sidecar/name-index system used to, so the
// collision this guards against hasn't been hit in practice -- but a
// caller submitting the SAME slug under two different locations in one
// server lifetime would get this wrong. Flagged, not fixed, pending a
// decision on whether familyLocation (not just Slug) should be the cache
// key everywhere, mirroring tree.py's sidecar_key_for fix for the same
// underlying slug-collision class of bug.
func (s *store) get(loc familyLocation) (*familyState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if fs, ok := s.families[loc.Slug]; ok {
		fs.mu.Lock()
		stale := !fs.dirty && fs.changedOnDisk()
		fs.mu.Unlock()
		if !stale {
			return fs, nil
		}
		// Rewritten by something else since we loaded it (a maintenance
		// pass, a removal script). Using the cached copy would write that
		// change away on the next flush -- found 2026-10-29 when two
		// cross-kingdom-homonym removals in Ichneumonidae were silently
		// restored. Drop it and reload from disk.
		log.Printf("reloading %s: changed on disk since it was cached", loc.Slug)
		delete(s.families, loc.Slug)
	}
	fs, err := loadFamily(s.root, loc, s.registry)
	if err != nil {
		return nil, err
	}
	fs.attachIndex(s.index, loc.Kingdom, loc)
	s.families[loc.Slug] = fs
	return fs, nil
}

// applyImport resolves cross-family matches before handing whatever's left
// to the target family's own apply(). Each family lock is acquired and
// fully released before the next is touched -- never two held at once by
// this goroutine -- so two concurrent requests that each find a match in
// the other's family can't deadlock. See crossfamily.go for why this
// exists: a species the global index already knows about, in some OTHER
// family, is merged there instead of being added a second time here, which
// is the exact failure mode behind the 2026-10-18 incident.
func (s *store) applyImport(loc familyLocation, req importRequest) (importResult, error) {
	targetFs, err := s.get(loc)
	if err != nil {
		return importResult{}, err
	}

	result := importResult{Added: []speciesResult{}, Merged: []speciesResult{}}
	remaining := req.Species[:0:0] // fresh slice; req.Species is the caller's

	for _, sp := range req.Species {
		other, found := s.index.lookup(req.Kingdom, sp)
		if !found || other == loc {
			remaining = append(remaining, sp)
			continue
		}
		otherFs, err := s.get(other)
		if err != nil {
			remaining = append(remaining, sp)
			continue
		}
		merged := otherFs.mergeExisting(sp)
		if merged == nil {
			// Index said it lived here; it didn't. Stale entry (e.g. the
			// on-disk record was removed by something outside this
			// service) -- fall back to local rather than dropping it.
			remaining = append(remaining, sp)
			continue
		}
		s.index.record(req.Kingdom, merged, other)
		result.Merged = append(result.Merged, speciesResult{
			Name: sp.str("name"), ID: merged.str("id"), UUID: merged.str("uuid"), Family: other.Slug,
		})
	}

	req.Species = remaining
	local := targetFs.apply(req)
	result.Added = append(result.Added, local.Added...)
	result.Merged = append(result.Merged, local.Merged...)
	result.GenusNew = local.GenusNew
	return result, nil
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
