package main

import "sync"

// globalIndex is a kingdom-scoped lookup of every species identity this
// server has seen -- by external (source,id) pairs first, normalized name
// second -- mapping to the family it currently lives in. This is what
// makes two importers submitting the same species into different families
// land in one place instead of silently creating a second copy, which is
// the exact failure mode behind the 2026-10-18 incident: two independent
// dedupe passes each decided a different family should keep a disputed
// species, and because the edits landed in different files, nothing caught
// the disagreement before 35 species vanished from both.
//
// Built incrementally as families are loaded and written, not by walking
// the whole tree at startup: this service only ever needs to know about
// families it has actually touched this session (see README's "narrow by
// design"). A species in a family this process has never loaded is
// invisible to it until that family is loaded -- by this import or a
// later one -- same as the per-family genusIndex already works.
//
// Matching is scoped per kingdom, same as dedupeSpeciesAcrossFamilies.py's
// own by_authority index: a name shared across kingdoms is a homonym
// (Graphium sarpedon is a butterfly in one kingdom and a fungus in
// another), never a duplicate.
type globalIndex struct {
	mu     sync.Mutex
	byID   map[string]familyLocation // kingdom + "|" + importKey.token()
	byName map[string]familyLocation // kingdom + "|" + normalizeName(name)
}

func newGlobalIndex() *globalIndex {
	return &globalIndex{byID: map[string]familyLocation{}, byName: map[string]familyLocation{}}
}

// lookup returns the family a species identity is already known to live
// in, if any. Checked by the caller against its own target family before
// deciding to merge elsewhere -- a hit pointing at the family already being
// written to just means "already known," not "move it."
func (g *globalIndex) lookup(kingdom string, sp *onode) (familyLocation, bool) {
	g.mu.Lock()
	defer g.mu.Unlock()
	for _, k := range sourceIDPairs(sp) {
		if loc, ok := g.byID[kingdom+"|"+k.token()]; ok {
			return loc, true
		}
	}
	if name := normalizeName(sp.str("name")); name != "" {
		if loc, ok := g.byName[kingdom+"|"+name]; ok {
			return loc, true
		}
	}
	return familyLocation{}, false
}

// record registers (or updates) where a species identity lives. Called at
// every point a species is added or merged -- within a genus, across a
// sibling genus, or across families -- so the index never falls behind
// what's actually on disk for families this process has loaded.
func (g *globalIndex) record(kingdom string, sp *onode, loc familyLocation) {
	g.mu.Lock()
	defer g.mu.Unlock()
	for _, k := range sourceIDPairs(sp) {
		g.byID[kingdom+"|"+k.token()] = loc
	}
	if name := normalizeName(sp.str("name")); name != "" {
		g.byName[kingdom+"|"+name] = loc
	}
}
