package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

// normalizeName is the dedupe identity: lower-cased, trimmed, with the
// stray leading/trailing quote characters some imported sources carry
// (e.g. `"Prionailurus`) stripped. Matching on name is deliberately the
// whole of the identity logic for this first cut — see the service README
// for why, and what a stronger identity (sourceIds / GBIF key) would need.
func normalizeName(name string) string {
	s := strings.TrimSpace(name)
	s = strings.Trim(s, `"'`)
	return strings.ToLower(s)
}

// mergeSpecies folds incoming into existing in place, preferring richer data
// without discarding anything existing already had.
func mergeSpecies(existing, incoming *onode) {
	existingDesc := existing.str("description")
	incomingDesc := incoming.str("description")
	if existingDesc == "" && incomingDesc != "" {
		existing.set("description", incomingDesc)
	} else if len(existingDesc) < len(incomingDesc) {
		existing.set("description", incomingDesc)
	}

	existingSource := existing.str("sourcedFrom")
	incomingSource := incoming.str("sourcedFrom")
	if (existingSource == "" || existingSource == "ollama") && incomingSource != "" && incomingSource != "ollama" {
		existing.set("sourcedFrom", incomingSource)
	}

	if continents := unionStrings(existing.get("continents"), incoming.get("continents")); continents != nil {
		existing.set("continents", continents)
	}

	if merged := mergeObjectField(existing.get("sourceIds"), incoming.get("sourceIds")); merged != nil {
		existing.set("sourceIds", merged)
	}

	if existing.str("uuid") == "" && incoming.str("uuid") != "" {
		existing.set("uuid", incoming.get("uuid"))
	}
	if existing.get("subspeciesCount") == nil && incoming.get("subspeciesCount") != nil {
		existing.set("subspeciesCount", incoming.get("subspeciesCount"))
	}
}

func unionStrings(a, b any) []any {
	seen := map[string]bool{}
	out := []any{}
	add := func(v any) {
		arr, ok := v.([]any)
		if !ok {
			return
		}
		for _, x := range arr {
			s, ok := x.(string)
			if !ok || seen[s] {
				continue
			}
			seen[s] = true
			out = append(out, x)
		}
	}
	add(a)
	add(b)
	if len(out) == 0 {
		return nil
	}
	return out
}

// genusRef is the minimal context an importer sends to place species under
// the right genus; everything else about the genus node passes through.
type genusRef struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Rank        string `json:"rank,omitempty"`
	SourcedFrom string `json:"sourcedFrom,omitempty"`
	Lineage     string `json:"lineage,omitempty"`
	Description string `json:"description,omitempty"`
}

type importRequest struct {
	Kingdom string   `json:"kingdom"`
	Phylum  string   `json:"phylum,omitempty"`
	Class   string   `json:"class,omitempty"`
	Order   string   `json:"order,omitempty"`
	Genus   genusRef `json:"genus"`
	Species []*onode `json:"species"`
}

type importResult struct {
	Added    []string `json:"added"`
	Merged   []string `json:"merged"`
	GenusNew bool     `json:"genusCreated"`
}

// familyState is the in-memory working copy of one family's JSON tree. Held
// only while a family is actively being written to; see store's idle
// eviction.
type familyState struct {
	mu        sync.Mutex
	slug      string
	file      string
	root      *onode
	dirty     bool
	lastWrite time.Time
	// genusIndex maps normalized genus name -> the live genus node, so a
	// repeat import into the same genus doesn't rescan every write.
	genusIndex map[string]*onode
}

func loadFamily(root string, loc familyLocation) (*familyState, error) {
	file, existed := resolveFamilyFile(root, loc)
	rootNode := &onode{}
	if existed {
		raw, err := os.ReadFile(file)
		if err != nil {
			return nil, fmt.Errorf("reading %s: %w", file, err)
		}
		if err := json.Unmarshal(raw, rootNode); err != nil {
			return nil, fmt.Errorf("parsing %s: %w", file, err)
		}
	} else {
		rootNode = newONode()
		rootNode.set("id", "FAM_"+strings.ToUpper(loc.Slug))
		rootNode.set("name", loc.Slug)
		rootNode.set("rank", "FAMILY")
		rootNode.set("children", []any{})
	}

	fs := &familyState{
		slug:       loc.Slug,
		file:       file,
		root:       rootNode,
		genusIndex: map[string]*onode{},
	}
	for _, g := range rootNode.children() {
		fs.genusIndex[normalizeName(g.str("name"))] = g
	}
	return fs, nil
}

// apply runs one importRequest against the family under its lock, merging
// or appending each incoming species into the target genus.
func (fs *familyState) apply(req importRequest) importResult {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	result := importResult{Added: []string{}, Merged: []string{}}

	genusKey := normalizeName(req.Genus.Name)
	genus, ok := fs.genusIndex[genusKey]
	if !ok {
		genus = newONode()
		genus.set("id", req.Genus.ID)
		genus.set("name", req.Genus.Name)
		genus.set("rank", "GENUS")
		if req.Genus.SourcedFrom != "" {
			genus.set("sourcedFrom", req.Genus.SourcedFrom)
		}
		if req.Genus.Lineage != "" {
			genus.set("lineage", req.Genus.Lineage)
		}
		if req.Genus.Description != "" {
			genus.set("description", req.Genus.Description)
		}
		genus.set("children", []any{})
		fs.genusIndex[genusKey] = genus
		children := fs.root.children()
		children = append(children, genus)
		fs.root.setChildren(children)
		result.GenusNew = true
	}

	speciesIndex := map[string]*onode{}
	genusChildren := genus.children()
	for _, sp := range genusChildren {
		speciesIndex[normalizeName(sp.str("name"))] = sp
	}

	for _, incoming := range req.Species {
		key := normalizeName(incoming.str("name"))
		if key == "" {
			continue
		}
		if existing, found := speciesIndex[key]; found {
			mergeSpecies(existing, incoming)
			result.Merged = append(result.Merged, incoming.str("name"))
			continue
		}
		genusChildren = append(genusChildren, incoming)
		speciesIndex[key] = incoming
		result.Added = append(result.Added, incoming.str("name"))
	}
	genus.setChildren(genusChildren)

	if len(result.Added) > 0 || len(result.Merged) > 0 {
		fs.dirty = true
		fs.lastWrite = time.Now()
	}
	return result
}

// flush writes the family back to disk as pretty JSON, matching the
// formatting buildData.ts and the rest of the tooling already expects, and
// preserving each object's original key order (see ojson.go) so a merge
// that changes no data produces no diff noise.
func (fs *familyState) flush() (bool, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()
	if !fs.dirty {
		return false, nil
	}
	out, err := marshalIndentNoEscape(fs.root, "  ")
	if err != nil {
		return false, err
	}
	if err := os.MkdirAll(dirOf(fs.file), 0o755); err != nil {
		return false, err
	}
	if err := os.WriteFile(fs.file, out, 0o644); err != nil {
		return false, err
	}
	fs.dirty = false
	return true, nil
}

func dirOf(file string) string {
	i := strings.LastIndex(file, string(os.PathSeparator))
	if i < 0 {
		return "."
	}
	return file[:i]
}
