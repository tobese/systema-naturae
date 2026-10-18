package main

import (
	"crypto/rand"
	"fmt"
)

// newUUIDv4 assigns a species' permanent identity: random, generated once
// when the arbiter first creates the node, never recomputed.
//
// This is deliberately not the v5-over-rank-path scheme buildData.ts uses
// for backfilling existing nodes (kingdom|phylum|class|order|family|genus|
// species|authorship, hashed). That scheme is a content fingerprint, not a
// stable identity -- it bakes in placement, so a species moved to a
// different family (exactly what the cross-family arbiter in this service
// exists to get right, see identity.go) would get a *different* uuid under
// it, even though it's the same species. mergeSpecies' existing rule --
// keep the existing uuid, only take incoming's if existing has none -- only
// gives you stability if the *first* assignment doesn't depend on mutable
// fields. A random v4 costs nothing to generate and has nothing to go stale.
func newUUIDv4() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		// crypto/rand failing is a kernel-level problem the caller can't
		// meaningfully recover from either; panic rather than silently
		// hand out a zero-value uuid that would collide with every other
		// failure at the same instant.
		panic("newUUIDv4: crypto/rand: " + err.Error())
	}
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant 10
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}
