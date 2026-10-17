package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

// node is a generic TaxonNode. The real shape (shared/src/types.ts) has ~30
// optional fields; a passthrough map avoids a second struct definition that
// drifts from the TypeScript one, and lets fields we don't know about round
// trip untouched.
type node map[string]any

func (n node) str(key string) string {
	if v, ok := n[key].(string); ok {
		return v
	}
	return ""
}

func (n node) children() []node {
	raw, ok := n["children"].([]any)
	if !ok {
		return nil
	}
	out := make([]node, 0, len(raw))
	for _, c := range raw {
		if m, ok := c.(map[string]any); ok {
			out = append(out, node(m))
		}
	}
	return out
}

func (n node) setChildren(cs []node) {
	raw := make([]any, len(cs))
	for i, c := range cs {
		raw[i] = map[string]any(c)
	}
	n["children"] = raw
}

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
func mergeSpecies(existing, incoming node) {
	if existing.str("description") == "" && incoming.str("description") != "" {
		existing["description"] = incoming["description"]
	} else if len(existing.str("description")) < len(incoming.str("description")) {
		existing["description"] = incoming["description"]
	}

	existingSource := existing.str("sourcedFrom")
	incomingSource := incoming.str("sourcedFrom")
	if (existingSource == "" || existingSource == "ollama") && incomingSource != "" && incomingSource != "ollama" {
		existing["sourcedFrom"] = incomingSource
	}

	existing["continents"] = unionStrings(existing["continents"], incoming["continents"])

	existingIDs, _ := existing["sourceIds"].(map[string]any)
	incomingIDs, _ := incoming["sourceIds"].(map[string]any)
	if incomingIDs != nil {
		merged := map[string]any{}
		for k, v := range existingIDs {
			merged[k] = v
		}
		for k, v := range incomingIDs {
			merged[k] = v
		}
		existing["sourceIds"] = merged
	}

	if existing.str("uuid") == "" && incoming.str("uuid") != "" {
		existing["uuid"] = incoming["uuid"]
	}
	if _, ok := existing["subspeciesCount"]; !ok {
		if v, ok := incoming["subspeciesCount"]; ok {
			existing["subspeciesCount"] = v
		}
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
	Species []node   `json:"species"`
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
	root      node
	dirty     bool
	lastWrite time.Time
	// genusIndex maps normalized genus name -> the live genus node, so a
	// repeat import into the same genus doesn't rescan every write.
	genusIndex map[string]node
}

func loadFamily(root string, loc familyLocation) (*familyState, error) {
	file, existed := resolveFamilyFile(root, loc)
	var rootNode node
	if existed {
		raw, err := os.ReadFile(file)
		if err != nil {
			return nil, fmt.Errorf("reading %s: %w", file, err)
		}
		var decoded map[string]any
		if err := json.Unmarshal(raw, &decoded); err != nil {
			return nil, fmt.Errorf("parsing %s: %w", file, err)
		}
		rootNode = node(decoded)
	} else {
		rootNode = node{
			"id":       "FAM_" + strings.ToUpper(loc.Slug),
			"name":     loc.Slug,
			"rank":     "FAMILY",
			"children": []any{},
		}
	}

	fs := &familyState{
		slug:       loc.Slug,
		file:       file,
		root:       rootNode,
		genusIndex: map[string]node{},
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
		genus = node{
			"id":       req.Genus.ID,
			"name":     req.Genus.Name,
			"rank":     "GENUS",
			"children": []any{},
		}
		if req.Genus.SourcedFrom != "" {
			genus["sourcedFrom"] = req.Genus.SourcedFrom
		}
		if req.Genus.Lineage != "" {
			genus["lineage"] = req.Genus.Lineage
		}
		if req.Genus.Description != "" {
			genus["description"] = req.Genus.Description
		}
		fs.genusIndex[genusKey] = genus
		children := fs.root.children()
		children = append(children, genus)
		fs.root.setChildren(children)
		result.GenusNew = true
	}

	speciesIndex := map[string]node{}
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
// formatting buildData.ts and the rest of the tooling already expects.
func (fs *familyState) flush() (bool, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()
	if !fs.dirty {
		return false, nil
	}
	out, err := json.MarshalIndent(map[string]any(fs.root), "", "  ")
	if err != nil {
		return false, err
	}
	out = append(out, '\n')
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
