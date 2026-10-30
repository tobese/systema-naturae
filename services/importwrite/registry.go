package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// unregisteredFamilyError means a request named a family slug that doesn't
// exist on disk AND isn't registered under its kingdom's taxonomy skeleton
// (portal/data/taxonomy.json or the kingdom-specific equivalent,
// kingdom-config.json's mapping -- same file importColChecklist.py's
// taxonomy_input() reads).
//
// Registration is the taxonomy decision (an appSlug and a colour theme, a
// human adding a new family on purpose); whether the DATA FILE for an
// already-registered family exists yet is a mechanical fact, safe to fix by
// creating it. Before this existed, loadFamily() couldn't tell the two
// apart -- any slug nobody had written a file for yet got a bare, orphaned
// family file created on the spot, no appSlug, invisible to buildData.ts's
// graft (which only ever finds a family by walking taxonomy.json's own
// appSlug entries). That's the exact inverse of the already-known
// Scaffolding Gaps bug (appSlug registered, no file -> species vanish) --
// same bug class, opposite direction, and this service's own README's "not
// touching taxonomy.json -- adding a brand-new family stays a manual,
// reviewed edit" was aspirational, not enforced, until this.
type unregisteredFamilyError struct {
	Kingdom string
	Slug    string
}

func (e *unregisteredFamilyError) Error() string {
	return fmt.Sprintf("family %q is not registered under kingdom %q -- "+
		"refusing to create a new family file for it. Register it (appSlug "+
		"+ colour theme) first, or treat this as a pending family.",
		e.Slug, e.Kingdom)
}

type kingdomConfig struct {
	Kingdoms map[string]struct {
		Input string `json:"input"`
	} `json:"kingdoms"`
}

// familyRegistry caches, per kingdom, the set of appSlugs that taxonomy.json
// (or the kingdom's equivalent) actually registers. Loaded once per kingdom,
// not per request -- these files are the tree's skeleton (families + their
// appSlug/speciesCount, no species-level data), a few MB at most, not
// something worth re-reading on every import.
type familyRegistry struct {
	mu     sync.Mutex
	byKing map[string]map[string]bool // kingdom -> set of registered appSlugs
}

func newFamilyRegistry() *familyRegistry {
	return &familyRegistry{byKing: map[string]map[string]bool{}}
}

func (r *familyRegistry) isRegistered(root, kingdom, slug string) (bool, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	slugs, ok := r.byKing[kingdom]
	if !ok {
		var err error
		slugs, err = loadRegisteredSlugs(root, kingdom)
		if err != nil {
			return false, err
		}
		r.byKing[kingdom] = slugs
	}
	return slugs[slug], nil
}

func loadRegisteredSlugs(root, kingdom string) (map[string]bool, error) {
	cfgPath := filepath.Join(root, "portal", "data", "kingdom-config.json")
	raw, err := os.ReadFile(cfgPath)
	if err != nil {
		return nil, fmt.Errorf("reading %s: %w", cfgPath, err)
	}
	var cfg kingdomConfig
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", cfgPath, err)
	}
	input := cfg.Kingdoms[kingdom].Input
	if _, ok := cfg.Kingdoms[kingdom]; !ok {
		if input = bacteriaVirusesInput[kingdom]; input == "" {
			return nil, fmt.Errorf("kingdom %q is not in %s", kingdom, cfgPath)
		}
	}

	taxPath := filepath.Join(root, "portal", input)
	taxRaw, err := os.ReadFile(taxPath)
	if err != nil {
		return nil, fmt.Errorf("reading %s: %w", taxPath, err)
	}
	var taxRoot onode
	if err := json.Unmarshal(taxRaw, &taxRoot); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", taxPath, err)
	}

	slugs := map[string]bool{}
	var walk func(n *onode)
	walk = func(n *onode) {
		if n.str("rank") == "FAMILY" {
			if slug := n.str("appSlug"); slug != "" {
				slugs[slug] = true
			}
		}
		for _, c := range n.children() {
			walk(c)
		}
	}
	walk(&taxRoot)
	return slugs, nil
}
