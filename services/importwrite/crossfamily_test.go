package main

import (
	"sync"
	"testing"
	"time"
)

func TestApply_FindsMatchInSiblingGenusSameFamily(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Oldgenus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Testus revised", "sourceIds": nodeFrom(map[string]any{"gbif": "42"}),
		})},
	})

	// Same family, DIFFERENT genus, same GBIF key -- a revision moving the
	// species, submitted the way a real importer would: it only knows the
	// genus it resolved, not that this family already holds the species
	// under a different one.
	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Newgenus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Testus revised", "sourceIds": nodeFrom(map[string]any{"gbif": "42"}),
			"description": "A description from the revision.",
		})},
	})

	if len(result.Added) != 0 || len(result.Merged) != 1 {
		t.Fatalf("expected a sibling-genus merge, not an add, got %+v", result)
	}
	if genus := fs.genusIndex["newgenus"]; genus != nil && len(genus.children()) != 0 {
		t.Fatalf("expected Newgenus to hold nothing -- the species should have merged into Oldgenus, got %d children", len(genus.children()))
	}
	oldGenus := fs.genusIndex["oldgenus"]
	if len(oldGenus.children()) != 1 {
		t.Fatalf("expected exactly one species in Oldgenus after the merge, got %d", len(oldGenus.children()))
	}
	if oldGenus.children()[0].str("description") != "A description from the revision." {
		t.Fatalf("expected the merge to carry the new description across, got %q", oldGenus.children()[0].str("description"))
	}
}

func TestApplyImport_CrossFamilyMergesIntoExistingLocation(t *testing.T) {
	root := t.TempDir()
	locA := familyLocation{Kingdom: "animalia", Phylum: "arthropoda", Class: "copepoda", Order: "harpacticoida", Slug: "miraciidae"}
	locB := familyLocation{Kingdom: "animalia", Phylum: "arthropoda", Class: "copepoda", Order: "incertae_sedis", Slug: "diosaccidae"}
	writeFixtureFamily(t, root, locA, map[string]any{"id": "FAM_MIRACIIDAE", "name": "Miraciidae", "rank": "FAMILY", "children": []any{}})
	writeFixtureFamily(t, root, locB, map[string]any{"id": "FAM_DIOSACCIDAE", "name": "Diosaccidae", "rank": "FAMILY", "children": []any{}})

	st := newStore(root, false, 0)

	// First import: species lands in family A (miraciidae), exactly the
	// 2026-10-18 incident's setup -- one pass files it here.
	first, err := st.applyImport(locA, importRequest{
		Kingdom: "animalia", Phylum: "arthropoda", Class: "copepoda", Order: "harpacticoida",
		Genus: genusRef{Name: "Amonardia"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Amonardia similis", "sourceIds": nodeFrom(map[string]any{"worms": "129871"}),
		})},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(first.Added) != 1 {
		t.Fatalf("expected the first import to add, got %+v", first)
	}

	// Second import: a DIFFERENT pass, independently, submits the SAME
	// species (same worms id) into family B (diosaccidae) -- exactly the
	// disagreement that silently lost 35 species on 2026-10-18, because
	// nothing before this checked across families at write time.
	second, err := st.applyImport(locB, importRequest{
		Kingdom: "animalia", Phylum: "arthropoda", Class: "copepoda", Order: "incertae_sedis",
		Genus: genusRef{Name: "Diosaccus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Amonardia similis", "sourceIds": nodeFrom(map[string]any{"worms": "129871"}),
			"description": "From the second pass.",
		})},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(second.Added) != 0 {
		t.Fatalf("expected NO add into diosaccidae -- the species already exists in miraciidae, got %+v", second)
	}
	if len(second.Merged) != 1 || second.Merged[0].Family != "miraciidae" {
		t.Fatalf("expected a merge reported against miraciidae, got %+v", second)
	}

	diosaccidaeFs, _ := st.get(locB)
	genus := diosaccidaeFs.genusIndex["diosaccus"]
	if genus != nil && len(genus.children()) != 0 {
		t.Fatalf("expected diosaccidae's Diosaccus genus to hold nothing -- no duplicate should have been created, got %d children", len(genus.children()))
	}

	miraciidaeFs, _ := st.get(locA)
	amonardia := miraciidaeFs.genusIndex["amonardia"]
	if len(amonardia.children()) != 1 {
		t.Fatalf("expected exactly one Amonardia species in miraciidae, got %d", len(amonardia.children()))
	}
	if amonardia.children()[0].str("description") != "From the second pass." {
		t.Fatalf("expected the second pass's description to have merged into the existing record, got %q", amonardia.children()[0].str("description"))
	}
}

func TestApplyImport_UnrelatedSpeciesStillAddsNormally(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{}})
	st := newStore(root, false, 0)

	result, err := st.applyImport(loc, importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus novus"})},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Added) != 1 || result.Added[0].Family != "" {
		t.Fatalf("expected a plain local add with no Family override, got %+v", result)
	}
}

func TestStore_CrossKingdomHomonymNotTreatedAsDuplicate(t *testing.T) {
	// dedupeSpeciesAcrossFamilies.py scopes its own identity matching per
	// kingdom for exactly this reason: Graphium sarpedon is a butterfly in
	// animalia and a fungus in fungi, sharing a name but not a taxon. The
	// global index must not merge across that boundary.
	root := t.TempDir()
	locAnimal := familyLocation{Kingdom: "animalia", Slug: "papilionidae"}
	locFungi := familyLocation{Kingdom: "fungi", Slug: "microascaceae"}
	writeFixtureFamily(t, root, locAnimal, map[string]any{"id": "FAM_PAPILIONIDAE", "name": "Papilionidae", "rank": "FAMILY", "children": []any{}})
	writeFixtureFamily(t, root, locFungi, map[string]any{"id": "FAM_MICROASCACEAE", "name": "Microascaceae", "rank": "FAMILY", "children": []any{}})
	st := newStore(root, false, 0)

	st.applyImport(locAnimal, importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Graphium"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Graphium sarpedon"})},
	})
	result, err := st.applyImport(locFungi, importRequest{
		Kingdom: "fungi", Genus: genusRef{Name: "Graphium"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Graphium sarpedon"})},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Added) != 1 {
		t.Fatalf("expected the fungal homonym to add independently, not merge across kingdoms, got %+v", result)
	}
}

func TestApplyImport_ConcurrentCrossFamilyLookupsDoNotDeadlock(t *testing.T) {
	// applyImport's whole safety argument is that this goroutine never holds
	// two family locks at once -- each is acquired and fully released
	// before the next. If that argument were wrong, two requests that each
	// find their match in the OTHER's family (A importing something B
	// already has, at the same moment B imports something A already has)
	// would deadlock: this reproduces exactly that shape, run many times
	// concurrently, and fails by hanging past the timeout rather than by an
	// assertion -- a real deadlock here has no other symptom.
	root := t.TempDir()
	locA := familyLocation{Kingdom: "animalia", Slug: "aaafamily"}
	locB := familyLocation{Kingdom: "animalia", Slug: "bbbfamily"}
	writeFixtureFamily(t, root, locA, map[string]any{"id": "FAM_A", "name": "Aaafamily", "rank": "FAMILY", "children": []any{}})
	writeFixtureFamily(t, root, locB, map[string]any{"id": "FAM_B", "name": "Bbbfamily", "rank": "FAMILY", "children": []any{}})
	st := newStore(root, false, 0)

	// Seed: "Species one" lives in A, "Species two" lives in B.
	st.applyImport(locA, importRequest{Kingdom: "animalia", Genus: genusRef{Name: "Genusone"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Species one"})}})
	st.applyImport(locB, importRequest{Kingdom: "animalia", Genus: genusRef{Name: "Genustwo"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Species two"})}})

	done := make(chan struct{})
	go func() {
		var wg sync.WaitGroup
		for i := 0; i < 200; i++ {
			wg.Add(2)
			// Goroutine 1: submits into B, but names species one -- its
			// match is in A.
			go func() {
				defer wg.Done()
				st.applyImport(locB, importRequest{Kingdom: "animalia", Genus: genusRef{Name: "Genusone"},
					Species: []*onode{nodeFrom(map[string]any{"name": "Species one"})}})
			}()
			// Goroutine 2: submits into A, but names species two -- its
			// match is in B. Same shape, opposite direction, at the same
			// time.
			go func() {
				defer wg.Done()
				st.applyImport(locA, importRequest{Kingdom: "animalia", Genus: genusRef{Name: "Genustwo"},
					Species: []*onode{nodeFrom(map[string]any{"name": "Species two"})}})
			}()
		}
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(10 * time.Second):
		t.Fatal("deadlock: concurrent cross-family lookups did not complete within 10s")
	}
}
