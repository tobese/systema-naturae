package main

import (
	"encoding/json"
	"fmt"
	"log"
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
	// Family is set only when the species was matched into a DIFFERENT
	// family than the one requested -- the store-level cross-family step,
	// not this file's own within-family matching. Empty means "landed where
	// the request asked."
	Family string `json:"family,omitempty"`
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
	// idx/kingdom/loc connect this family to the server-wide identity
	// index (crossfamily.go). idx is nil for a familyState created
	// directly by loadFamily in isolation (every existing test) -- apply()
	// guards every use, so cross-family/sibling-genus matching simply
	// doesn't run until attachIndex is called, which store.get does for
	// every family it loads.
	idx     *globalIndex
	kingdom string
	loc     familyLocation
	// diskMod/diskSize are the file's stat as of the last load or flush.
	// Anything else that rewrites the file (a maintenance pass, a removal
	// script) changes them, and a cached copy must not be written back
	// over that change -- see changedOnDisk.
	diskMod  time.Time
	diskSize int64
}

// changedOnDisk reports whether the family file was rewritten by someone
// else since this copy was loaded or last flushed. Caller holds fs.mu or
// owns fs exclusively.
func (fs *familyState) changedOnDisk() bool {
	info, err := os.Stat(fs.file)
	if err != nil {
		return !fs.diskMod.IsZero() // existed when loaded, gone now
	}
	return !info.ModTime().Equal(fs.diskMod) || info.Size() != fs.diskSize
}

func (fs *familyState) recordDiskStat() {
	if info, err := os.Stat(fs.file); err == nil {
		fs.diskMod, fs.diskSize = info.ModTime(), info.Size()
	}
}

// indexGenera maps every GENUS under n, at any depth, by normalized name.
// Families with a SUBFAMILY/TRIBE level keep their genera below the root;
// indexing only the root's children (as this used to) made every import
// into such a genus create a second, top-level genus of the same name and
// re-add species the nested one already held -- 303 genera in 245 families
// were split that way by 2026-10-29. A genus is not descended into. If a
// name occurs twice (an already-split family), the copy holding more
// species wins, so new imports land in the established placement.
func indexGenera(n *onode, idx map[string]*onode) {
	for _, c := range n.children() {
		if c.str("rank") != "GENUS" {
			indexGenera(c, idx)
			continue
		}
		key := normalizeName(c.str("name"))
		if prev, ok := idx[key]; ok && len(prev.children()) >= len(c.children()) {
			continue
		}
		idx[key] = c
	}
}

// countSpecies counts SPECIES nodes at any depth, children and speciesList
// alike -- the same definition as scripts/tree.py's count_species, which
// verifyTree checks every family file's declared speciesCount against.
func countSpecies(n *onode) int {
	c := 0
	if n.str("rank") == "SPECIES" {
		c++
	}
	for _, key := range []string{"children", "speciesList"} {
		raw, _ := n.get(key).([]any)
		for _, x := range raw {
			if o, ok := x.(*onode); ok {
				c += countSpecies(o)
			}
		}
	}
	return c
}

// attachIndex connects this family to the server-wide identity index and
// registers everything already on disk under it, so a LATER import
// touching a different family can find species that were here before this
// service ever loaded this file. Called once, right after a family is
// first loaded (store.get) -- safe to call again, just redundant.
func (fs *familyState) attachIndex(idx *globalIndex, kingdom string, loc familyLocation) {
	fs.idx = idx
	fs.kingdom = kingdom
	fs.loc = loc
	if idx == nil {
		return
	}
	for _, g := range fs.genusIndex {
		for _, sp := range g.children() {
			idx.record(kingdom, sp, loc)
		}
	}
}

// loadFamily reads (or, for a registered-but-not-yet-written family,
// creates) one family's root node. `registry` is nil in every existing test
// (they write their own fixture first, so `existed` is always true there and
// the check below never runs) -- the real store.go call site is the only
// one that needs the safety on, since it's the only path that can reach a
// slug nobody has ever written a file for.
func loadFamily(root string, loc familyLocation, registry *familyRegistry) (*familyState, error) {
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
		if registry != nil {
			ok, err := registry.isRegistered(root, loc.Kingdom, loc.Slug)
			if err != nil {
				return nil, fmt.Errorf("checking registration for %s/%s: %w", loc.Kingdom, loc.Slug, err)
			}
			if !ok {
				return nil, &unregisteredFamilyError{Kingdom: loc.Kingdom, Slug: loc.Slug}
			}
		}
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
	indexGenera(rootNode, fs.genusIndex)
	if existed {
		fs.recordDiskStat()
	}
	return fs, nil
}

// byIdentity builds a (by-id, by-name) lookup over one genus's children,
// the same shape apply()'s main loop already builds for the target genus --
// factored out so findInOtherGenera and mergeExisting can reuse it instead
// of drifting from the matching rules used for the common case.
func byIdentity(children []*onode) (map[string]*onode, map[string]*onode) {
	byID := map[string]*onode{}
	byName := map[string]*onode{}
	for _, sp := range children {
		indexByID(byID, sp)
		byName[normalizeName(sp.str("name"))] = sp
	}
	return byID, byName
}

func matchIn(children []*onode, incoming *onode) *onode {
	byID, byName := byIdentity(children)
	if m := matchByID(byID, incoming); m != nil {
		return m
	}
	return byName[normalizeName(incoming.str("name"))]
}

// findInOtherGenera searches every genus in this family OTHER than the one
// already checked by apply()'s main loop, for a match by ID then by
// normalized name. Catches a species submitted under a different genus
// than the one it's already filed under within the SAME family -- a
// taxonomic revision moving it between genera, or two importers
// disagreeing about which genus is right -- the same "two places claim
// this species" problem a cross-family duplicate is, just one level
// narrower. Caller already holds fs.mu.
func (fs *familyState) findInOtherGenera(incoming *onode, skipGenusKey string) *onode {
	for key, g := range fs.genusIndex {
		if key == skipGenusKey {
			continue
		}
		if m := matchIn(g.children(), incoming); m != nil {
			return m
		}
	}
	return nil
}

// mergeExisting finds incoming's match anywhere in this family (any genus)
// and merges into it -- used by the store-level cross-family step, where
// the global index says the species already lives in THIS family but not
// which genus. Returns the merged node, or nil if the index was stale and
// nothing was actually found (e.g. the on-disk record was removed by
// something outside this service) -- the caller falls back to treating
// the submission as new rather than dropping it.
func (fs *familyState) mergeExisting(incoming *onode) *onode {
	fs.mu.Lock()
	defer fs.mu.Unlock()
	for _, g := range fs.genusIndex {
		if existing := matchIn(g.children(), incoming); existing != nil {
			mergeSpecies(existing, incoming)
			fs.dirty = true
			fs.lastWrite = time.Now()
			return existing
		}
	}
	return nil
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
			if fs.idx != nil {
				fs.idx.record(fs.kingdom, existing, fs.loc)
			}
			result.Merged = append(result.Merged, speciesResult{Name: name, ID: existing.str("id"), UUID: existing.str("uuid")})
			continue
		}

		// Not filed under the target genus. Before concluding it's new,
		// check every OTHER genus in this same family -- see
		// findInOtherGenera's doc comment for why that's not redundant with
		// the store-level cross-family check (a different FAMILY, this is a
		// different GENUS in the one already loaded and locked here).
		if sibling := fs.findInOtherGenera(incoming, genusKey); sibling != nil {
			mergeSpecies(sibling, incoming)
			if fs.idx != nil {
				fs.idx.record(fs.kingdom, sibling, fs.loc)
			}
			result.Merged = append(result.Merged, speciesResult{Name: name, ID: sibling.str("id"), UUID: sibling.str("uuid")})
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
		if fs.idx != nil {
			fs.idx.record(fs.kingdom, incoming, fs.loc)
		}
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
	// speciesCount is read by the Coverage modal and by verifyTree.py's own
	// "family data file speciesCount matches its contents" gate --
	// importColChecklist.py's direct-write path recomputes and stamps it on
	// every apply, but this service never did, so a family touched only
	// through importwrite silently drifted out of sync with its own file's
	// contents (caught 2026-10-19 on the first real split-pipeline import:
	// 20 files disagreed, worst case Dakuidae declaring 41 against 47 held).
	// Recomputed here rather than in apply(), so it reflects the species
	// actually being written, not a running tally that could drift from it.
	// Counted at every depth (subfamily/tribe levels, speciesList) -- the
	// genus-children-only count this used to do understated any family
	// with a subfamily level.
	n := countSpecies(fs.root)
	declared := -1 // never equals a real count, so a missing/odd-typed field still gets set
	switch v := fs.root.get("speciesCount").(type) {
	case float64:
		declared = int(v)
	case int:
		declared = v
	}
	if declared != n {
		fs.root.set("speciesCount", n)
	}
	out, err := marshalIndentNoEscape(fs.root, "  ")
	if err != nil {
		return false, err
	}
	if err := os.MkdirAll(dirOf(fs.file), 0o755); err != nil {
		return false, err
	}
	if fs.changedOnDisk() {
		// The clean case is handled in store.get (reload before use); a
		// dirty copy means an external write landed inside one flush
		// interval. Writing wins, but loudly, so it can be checked.
		log.Printf("WARNING: %s changed on disk while %d-second-old writes were pending; overwriting the external change", fs.file, int(time.Since(fs.lastWrite).Seconds()))
	}
	// Temp file + rename: a reader (verifyTree, a maintenance script) never
	// sees a half-written family file.
	tmp, err := os.CreateTemp(dirOf(fs.file), ".importwrite-*.tmp")
	if err != nil {
		return false, err
	}
	if _, err := tmp.Write(out); err != nil {
		tmp.Close()
		os.Remove(tmp.Name())
		return false, err
	}
	tmp.Close()
	os.Chmod(tmp.Name(), 0o644)
	if err := os.Rename(tmp.Name(), fs.file); err != nil {
		os.Remove(tmp.Name())
		return false, err
	}
	fs.recordDiskStat()
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
