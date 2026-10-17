package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCandidatePaths_OmitsAbsentRanks(t *testing.T) {
	rel := candidatePaths(familyLocation{Kingdom: "Animalia", Slug: "tardigrada-fam"})
	want := filepath.Join("taxonomy", "animalia", "tardigrada-fam", "src", "data", "tardigrada-fam.json")
	if rel[len(rel)-1] != want {
		t.Fatalf("expected least-specific candidate %q, got %q", want, rel[len(rel)-1])
	}
}

func TestResolveFamilyFile_FallsBackToSearch(t *testing.T) {
	root := t.TempDir()
	// Simulate the viruses case: two extra levels (realm/kingdom) above
	// phylum that no candidate path models, so only the walk finds it.
	deep := filepath.Join(root, "taxonomy", "viruses", "some_realm", "some_kingdom", "some_phylum", "some_class", "some_order", "somefamily", "src", "data")
	if err := os.MkdirAll(deep, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(deep, "somefamily.json"), []byte("{}"), 0o644); err != nil {
		t.Fatal(err)
	}

	file, existed := resolveFamilyFile(root, familyLocation{Kingdom: "viruses", Slug: "somefamily"})
	if !existed {
		t.Fatalf("expected search fallback to find the file")
	}
	if file != filepath.Join(deep, "somefamily.json") {
		t.Fatalf("resolved to wrong file: %s", file)
	}
}

func TestResolveFamilyFile_NewFamilyFallsBackToPreferredPath(t *testing.T) {
	root := t.TempDir()
	file, existed := resolveFamilyFile(root, familyLocation{
		Kingdom: "animalia", Phylum: "chordata", Class: "mammalia", Order: "carnivora", Slug: "newfamily",
	})
	if existed {
		t.Fatalf("expected no existing file")
	}
	want := filepath.Join(root, "taxonomy", "animalia", "chordata", "mammalia", "carnivora", "newfamily", "src", "data", "newfamily.json")
	if file != want {
		t.Fatalf("expected %s, got %s", want, file)
	}
}

// TestResolveFamilyFile_MatchesRealTree checks the Go port against a few
// real families in the actual repo tree, so a future edit to either this
// file or portal/scripts/lib/familyPath.ts that makes them diverge gets
// caught here rather than failing silently in production, which is exactly
// the failure mode familyPath.ts's own doc comment warns about.
func TestResolveFamilyFile_MatchesRealTree(t *testing.T) {
	repoRoot := findRepoRoot(t)
	cases := []struct {
		loc  familyLocation
		want string
	}{
		{
			familyLocation{Kingdom: "animalia", Phylum: "chordata", Class: "mammalia", Order: "carnivora", Slug: "felidae"},
			filepath.Join(repoRoot, "taxonomy", "animalia", "chordata", "mammalia", "carnivora", "felidae", "src", "data", "felidae.json"),
		},
		{
			familyLocation{Kingdom: "animalia", Phylum: "chordata", Class: "aves", Order: "passeriformes", Slug: "corvidae"},
			filepath.Join(repoRoot, "taxonomy", "animalia", "chordata", "aves", "passeriformes", "corvidae", "src", "data", "corvidae.json"),
		},
	}
	for _, c := range cases {
		file, existed := resolveFamilyFile(repoRoot, c.loc)
		if !existed {
			t.Fatalf("%s: expected file to exist in real tree", c.loc.Slug)
		}
		if file != c.want {
			t.Fatalf("%s: got %s, want %s", c.loc.Slug, file, c.want)
		}
	}
}

func findRepoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 10; i++ {
		if _, err := os.Stat(filepath.Join(dir, "CLAUDE.md")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	t.Fatal("could not find repo root (no CLAUDE.md found above cwd)")
	return ""
}
