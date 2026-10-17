package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// writeFixtureFamily writes raw JSON bytes to simulate a pre-existing
// family file on disk. A plain map is fine here — these are "what's
// already on disk before the test," not something going through onode.
func writeFixtureFamily(t *testing.T, root string, loc familyLocation, body map[string]any) string {
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
	writeFixtureFamily(t, root, loc, map[string]any{
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
		Species: []*onode{
			nodeFrom(map[string]any{"id": "SP_PANTHERA_LEO", "name": "Panthera leo", "rank": "SPECIES", "sourcedFrom": "gbif"}),
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
	writeFixtureFamily(t, root, loc, map[string]any{
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
		Species: []*onode{
			nodeFrom(map[string]any{
				"id": "SP_PANTHERA_LEO_A", "name": "Panthera leo", "rank": "SPECIES",
				"sourcedFrom": "gbif", "continents": []any{"Africa"},
			}),
		},
	})

	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{ID: "GENUS_PANTHERA", Name: "Panthera"},
		Species: []*onode{
			nodeFrom(map[string]any{
				"id": "SP_PANTHERA_LEO_B", "name": "Panthera leo", "rank": "SPECIES",
				"sourcedFrom": "checklistbank", "description": "The lion.",
				"continents": []any{"Asia"},
			}),
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
	continents, _ := merged.get("continents").([]any)
	if len(continents) != 2 {
		t.Fatalf("expected continents unioned to 2, got %+v", continents)
	}
}

func TestApply_MatchesByGbifIDDespiteNameChange(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name":      "Testus antiquus", // the old, misspelled name
			"sourceIds": nodeFrom(map[string]any{"gbif": "2436351"}),
		})},
	})

	// A later import resolves the correct spelling under the same GBIF
	// usage key. Name-only matching would see this as a brand-new species
	// and duplicate it; ID matching must find the existing one instead.
	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name":        "Testus correctus",
			"sourceIds":   nodeFrom(map[string]any{"gbif": "2436351"}),
			"description": "The corrected name.",
		})},
	})

	if len(result.Added) != 0 || len(result.Merged) != 1 {
		t.Fatalf("expected the ID match to merge, not add, got %+v", result)
	}
	genus := fs.genusIndex["testus"]
	if len(genus.children()) != 1 {
		t.Fatalf("expected exactly one species after an ID match despite the name change, got %d", len(genus.children()))
	}
	merged := genus.children()[0]
	if merged.str("description") != "The corrected name." {
		t.Fatalf("expected the merge to carry over the new description, got %q", merged.str("description"))
	}
}

func TestApply_MatchesByIDFromStringArraySourceIds(t *testing.T) {
	// Real data shapes sourceIds inconsistently: col/itis/wikidata are
	// usually string arrays (a species can carry more than one historical
	// ID from the same source), checklistbank is usually a bare string.
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name":      "Testus originalis",
			"sourceIds": nodeFrom(map[string]any{"col": []any{"N5F3"}}),
		})},
	})

	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name":      "Testus renamed",
			"sourceIds": nodeFrom(map[string]any{"col": []any{"N5F3"}}),
		})},
	})

	if len(result.Added) != 0 || len(result.Merged) != 1 {
		t.Fatalf("expected the col ID (string array) to match, got %+v", result)
	}
}

func TestApply_FallsBackToNameWhenNeitherSideHasAnID(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus plainus"})},
	})
	result := fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus plainus", "sourcedFrom": "checklistbank"})},
	})

	if len(result.Added) != 0 || len(result.Merged) != 1 {
		t.Fatalf("expected name fallback to still dedupe with no IDs on either side, got %+v", result)
	}
}

func TestApply_PrefersNonOllamaSource(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus ollama-filled", "sourcedFrom": "ollama"})},
	})
	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus ollama-filled", "sourcedFrom": "gbif"})},
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
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{"name": "Testus novus"})},
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

// TestFlush_PreservesKeyOrder is the regression test for the diff-noise bug
// found by running the real importer against real data: re-flushing a
// family with no actual data changes must not reorder keys, or every
// import becomes a whole-file diff. See README's "Known issue found by
// that test."
func TestFlush_PreservesKeyOrder(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	original := `{
  "name": "Testidae",
  "id": "FAM_TESTIDAE",
  "rank": "FAMILY",
  "children": [
    {
      "name": "Testus",
      "id": "GENUS_TESTUS",
      "rank": "GENUS",
      "children": [
        {
          "name": "Testus existens",
          "id": "SP_EXISTENS",
          "rank": "SPECIES",
          "sourcedFrom": "gbif",
          "description": "Already here.",
          "children": []
        }
      ]
    }
  ]
}`
	file, _ := resolveFamilyFile(root, loc)
	if err := os.MkdirAll(filepath.Dir(file), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, []byte(original), 0o644); err != nil {
		t.Fatal(err)
	}

	fs, err := loadFamily(root, loc)
	if err != nil {
		t.Fatal(err)
	}

	// Submit the exact same species again, as a second importer run would.
	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{ID: "GENUS_TESTUS", Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Testus existens", "id": "SP_EXISTENS", "rank": "SPECIES", "sourcedFrom": "gbif",
		})},
	})
	fs.dirty = true // force a flush even though nothing actually changed, to check ordering
	if _, err := fs.flush(); err != nil {
		t.Fatal(err)
	}

	out, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}

	// Spot-check: "name" must still come before "id" at both the family and
	// species level, exactly as in the original file. encoding/json's
	// default map-based marshal would alphabetize ("children", "id",
	// "name", "rank"...) and fail this.
	text := string(out)
	nameIdx := indexOfOrFatal(t, text, `"name": "Testidae"`)
	idIdx := indexOfOrFatal(t, text, `"id": "FAM_TESTIDAE"`)
	if nameIdx > idIdx {
		t.Fatalf("expected family's \"name\" key to stay before \"id\", got:\n%s", text)
	}
	descIdx := indexOfOrFatal(t, text, `"description": "Already here."`)
	childrenIdx := indexOfOrFatal(t, text, `"children": []`)
	if descIdx > childrenIdx {
		t.Fatalf("expected species' \"description\" to stay before its \"children\", got:\n%s", text)
	}
}

// TestFlush_DoesNotHTMLEscape is the regression test for the second
// diff-noise source found by the same real-data run: Go's default JSON
// encoding escapes "&" to "&", and real authorship strings (e.g.
// "Anderson & Handley, 2001") contain literal "&".
func TestFlush_DoesNotHTMLEscape(t *testing.T) {
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Slug: "testidae"}
	writeFixtureFamily(t, root, loc, map[string]any{
		"id": "FAM_TESTIDAE", "name": "Testidae", "rank": "FAMILY", "children": []any{},
	})
	fs, _ := loadFamily(root, loc)

	fs.apply(importRequest{
		Kingdom: "animalia", Genus: genusRef{Name: "Testus"},
		Species: []*onode{nodeFrom(map[string]any{
			"name": "Testus novus", "authorship": "Anderson & Handley, 2001",
		})},
	})
	if _, err := fs.flush(); err != nil {
		t.Fatal(err)
	}

	raw, err := os.ReadFile(fs.file)
	if err != nil {
		t.Fatal(err)
	}
	text := string(raw)
	if indexOf(text, "\\u0026") >= 0 {
		t.Fatalf("expected literal \"&\", got HTML-escaped output:\n%s", text)
	}
	if indexOf(text, "Anderson & Handley, 2001") < 0 {
		t.Fatalf("expected literal authorship string, got:\n%s", text)
	}
}

func indexOfOrFatal(t *testing.T, haystack, needle string) int {
	t.Helper()
	i := indexOf(haystack, needle)
	if i < 0 {
		t.Fatalf("expected to find %q in:\n%s", needle, haystack)
	}
	return i
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}
