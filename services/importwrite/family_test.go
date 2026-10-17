package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func writeFixtureFamily(t *testing.T, root string, loc familyLocation, body node) string {
	t.Helper()
	file, _ := resolveFamilyFile(root, loc)
	if err := os.MkdirAll(filepath.Dir(file), 0o755); err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(body)
	if err := os.WriteFile(file, raw, 0o644); err != nil {
		t.Fatal(err)
	}
	return file
}

func TestApply_AddsNewSpecies(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Phylum: "chordata", Class: "mammalia", Order: "carnivora", Slug: "felidae"}
	writeFixtureFamily(t, root, loc, node{
		"id": "FAM_FELIDAE", "name": "Felidae", "rank": "FAMILY",
		"children": []any{},
	})

	fs, err := loadFamily(root, loc)
	if err != nil {
		t.Fatal(err)
	}

	result := fs.apply(importRequest{
		Kingdom: "animalia", Phylum: "chordata", Class: "mammalia", Order: "carnivora",
		Genus: genusRef{ID: "GENUS_PANTHERA", Name: "Panthera"},
		Species: []node{
			{"id": "SP_PANTHERA_LEO", "name": "Panthera leo", "rank": "SPECIES", "sourcedFrom": "gbif"},
		},
	})

	if len(result.Added) != 1 || result.Added[0] != "Panthera leo" {
		t.Fatalf("expected Panthera leo added, got %+v", result)
	}
	if !result.GenusNew {
		t.Fatalf("expected genus to be reported new")
	}

	genus := fs.genusIndex["panthera"]
	if genus == nil {
		t.Fatalf("genus not indexed")
	}
	if len(genus.children()) != 1 {
		t.Fatalf("expected 1 species under genus, got %d", len(genus.children()))
	}
}

func TestApply_DedupesByNormalizedName(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Phylum: "chordata", Class: "mammalia", Order: "carnivora", Slug: "felidae"}
	writeFixtureFamily(t, root, loc, node{
		"id": "FAM_FELIDAE", "name": "Felidae", "rank": "FAMILY",
		"children": []any{},
	})

	fs, err := loadFamily(root, loc)
	if err != nil {
		t.Fatal(err)
	}

	// Two "concurrent importers" both submit Panthera leo, one from GBIF
	// with a continent, one from ChecklistBank with a description. This is
	// the scenario that used to produce duplicate copies across a git merge.
	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{ID: "GENUS_PANTHERA", Name: "Panthera"},
		Species: []node{
			{"id": "SP_PANTHERA_LEO_A", "name": "Panthera leo", "rank": "SPECIES",
				"sourcedFrom": "gbif", "continents": []any{"Africa"}},
		},
	})

	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{ID: "GENUS_PANTHERA", Name: "Panthera"},
		Species: []node{
			{"id": "SP_PANTHERA_LEO_B", "name": "Panthera leo", "rank": "SPECIES",
				"sourcedFrom": "checklistbank", "description": "The lion.",
				"continents": []any{"Asia"}},
		},
	})

	if len(result.Added) != 0 || len(result.Merged) != 1 {
		t.Fatalf("expected a merge not an add, got %+v", result)
	}

	genus := fs.genusIndex["panthera"]
	if len(genus.children()) != 1 {
		t.Fatalf("expected exactly one Panthera leo after merge, got %d: %+v", len(genus.children()), genus.children())
	}

	merged := genus.children()[0]
	if merged.str("description") != "The lion." {
		t.Fatalf("expected merged description to survive, got %q", merged.str("description"))
	}
	continents, _ := merged["continents"].([]any)
	if len(continents) != 2 {
		t.Fatalf("expected continents unioned to 2, got %+v", continents)
	}
}

func TestApply_PrefersNonOllamaSource(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, node{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []node{{"name": "Testus ollama-filled", "sourcedFrom": "ollama"}},
	})
	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []node{{"name": "Testus ollama-filled", "sourcedFrom": "gbif"}},
	})

	genus := fs.genusIndex["testus"]
	merged := genus.children()[0]
	if merged.str("sourcedFrom") != "gbif" {
		t.Fatalf("expected gbif to replace ollama as sourcedFrom, got %q", merged.str("sourcedFrom"))
	}
}

func TestFlush_WritesAndClearsDirty(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, node{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []node{{"name": "Testus novus"}},
	})

	wrote, err := fs.flush()
	if err != nil {
		t.Fatal(err)
	}
	if !wrote {
		t.Fatalf("expected flush to report a write")
	}
	if fs.dirty {
		t.Fatalf("expected dirty to clear after flush")
	}

	raw, err := os.ReadFile(fs.file)
	if err != nil {
		t.Fatal(err)
	}
	var reread map[string]any
	if err := json.Unmarshal(raw, &reread); err != nil {
		t.Fatal(err)
	}
	children, _ := reread["children"].([]any)
	if len(children) != 1 {
		t.Fatalf("expected 1 genus on disk after flush, got %d", len(children))
	}

	// Flushing again with nothing dirty should be a no-op.
	wrote2, err := fs.flush()
	if err != nil {
		t.Fatal(err)
	}
	if wrote2 {
		t.Fatalf("expected second flush with no changes to report no write")
	}
}
