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

// speciesResult reports what a submitted species actually ended up as,
// uuid included -- so a transformer logging its own import run records the
// identity the arbiter assigned or confirmed, not the one it guessed.
type speciesResult struct {
	Name string `json:"name"`
	ID   string `json:"id"`
	UUID string `json:"uuid,omitempty"`
}

type importResult struct {
	Added    []speciesResult `json:"added"`
	Merged   []speciesResult `json:"merged"`
	GenusNew bool            `json:"genusCreated"`
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

	result := importResult{Added: []speciesResult{}, Merged: []speciesResult{}}

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

	speciesByName := map[string]*onode{}
	speciesByID := map[string]*onode{}
	genusChildren := genus.children()
	for _, sp := range genusChildren {
		speciesByName[normalizeName(sp.str("name"))] = sp
		indexByID(speciesByID, sp)
	}

	for _, incoming := range req.Species {
		name := incoming.str("name")
		key := normalizeName(name)
		if key == "" {
			continue
		}

		// A shared external ID (GBIF key, ChecklistBank URN, ...) is a
		// stronger signal than name and is tried first, so a later import
		// still finds the right species even if its name changed (a typo
		// fix, an author's spelling correction, a genus move). Falling
		// back to name covers the common case where neither side has
		// resolved any cross-reference ID yet.
		existing := matchByID(speciesByID, incoming)
		if existing == nil {
			existing = speciesByName[key]
		}

		if existing != nil {
			mergeSpecies(existing, incoming)
			speciesByName[normalizeName(existing.str("name"))] = existing
			indexByID(speciesByID, existing)
			result.Merged = append(result.Merged, speciesResult{Name: name, ID: existing.str("id"), UUID: existing.str("uuid")})
			continue
		}

		// A brand-new species gets its permanent identity here, once --
		// never re-derived from placement, so a later cross-family move
		// (mergeSpecies above, next time this id/name is submitted) can't
		// change it. See uuid.go.
		if incoming.str("uuid") == "" {
			incoming.set("uuid", newUUIDv4())
		}
		genusChildren = append(genusChildren, incoming)
		speciesByName[key] = incoming
		indexByID(speciesByID, incoming)
		result.Added = append(result.Added, speciesResult{Name: name, ID: incoming.str("id"), UUID: incoming.str("uuid")})
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
