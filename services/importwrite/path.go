package main

import (
	"os"
	"path/filepath"
	"strings"
)

// familyLocation mirrors FamilyLocation in portal/scripts/lib/familyPath.ts.
type familyLocation struct {
	Kingdom string
	Phylum  string
	Class   string
	Order   string
	Slug    string
}

// dirName mirrors dirName() in familyPath.ts: lower-case, spaces -> underscores.
func dirName(s string) string {
	return strings.ReplaceAll(strings.ToLower(strings.TrimSpace(s)), " ", "_")
}

// candidatePaths mirrors candidatePaths() in familyPath.ts: most-specific
// first, absent ranks omitted rather than defaulted.
//
// This MUST stay in lockstep with portal/scripts/lib/familyPath.ts, which is
// the single authority for family -> path resolution for every other writer
// in this repo (buildData.ts, fetchSpeciesFromApi.ts, bootstrapAnimalPhyla.ts,
// ...). A second implementation that silently drifts from the original is
// exactly the failure mode that file's own doc comment warns about. If you
// change one, change both and re-run path_test.go against the real tree.
func candidatePaths(loc familyLocation) []string {
	k := dirName(loc.Kingdom)
	p := dirName(loc.Phylum)
	c := dirName(loc.Class)
	o := dirName(loc.Order)

	tails := [][]string{
		{p, c, o, loc.Slug},
		{c, o, loc.Slug},
		{p, o, loc.Slug},
		{p, c, loc.Slug},
		{p, loc.Slug},
		{c, loc.Slug},
		{loc.Slug},
	}

	seen := map[string]bool{}
	out := []string{}
	for _, t := range tails {
		segs := []string{}
		for _, s := range t {
			if s != "" {
				segs = append(segs, s)
			}
		}
		if len(segs) == 0 {
			continue
		}
		parts := append([]string{"taxonomy", k}, segs...)
		parts = append(parts, "src", "data", loc.Slug+".json")
		rel := filepath.Join(parts...)
		if !seen[rel] {
			seen[rel] = true
			out = append(out, rel)
		}
	}
	return out
}

// resolveFamilyFile mirrors resolveFamilyFile() in familyPath.ts: try every
// candidate, fall back to a filesystem search (needed for the viruses
// kingdom's extra REALM/KINGDOM levels), and finally fall back to the
// most-preferred candidate path even if nothing exists yet (so a brand-new
// family can still be written).
func resolveFamilyFile(root string, loc familyLocation) (file string, existed bool) {
	candidates := candidatePaths(loc)
	for _, rel := range candidates {
		full := filepath.Join(root, rel)
		if _, err := os.Stat(full); err == nil {
			return full, true
		}
	}
	if found := searchFamilyFile(root, loc.Kingdom, loc.Slug); found != "" {
		return found, true
	}
	return filepath.Join(root, candidates[0]), false
}

// searchFamilyFile mirrors searchFamilyFile() in familyPath.ts: a bounded
// walk of the kingdom directory looking for src/data/<slug>.json. Safe
// because a slug is unique within a kingdom.
func searchFamilyFile(root, kingdom, slug string) string {
	target := slug + ".json"
	kingdomDir := filepath.Join(root, "taxonomy", dirName(kingdom))
	if _, err := os.Stat(kingdomDir); err != nil {
		return ""
	}
	var found string
	_ = filepath.WalkDir(kingdomDir, func(path string, d os.DirEntry, err error) error {
		if err != nil || found != "" {
			return nil
		}
		if d.IsDir() && d.Name() == "src" {
			candidate := filepath.Join(path, "data", target)
			if _, err := os.Stat(candidate); err == nil {
				found = candidate
			}
		}
		return nil
	})
	return found
}
