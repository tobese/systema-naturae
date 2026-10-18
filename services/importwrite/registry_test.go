package main

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// writeFixtureKingdomConfig writes a minimal portal/data/kingdom-config.json
// + the taxonomy skeleton it points to, registering exactly the given family
// slugs under one kingdom -- enough for familyRegistry.isRegistered to read
// without needing the real multi-megabyte taxonomy.json.
func writeFixtureKingdomConfig(t *testing.T, root, kingdom string, slugs []string) {
	t.Helper()
	portalData := filepath.Join(root, "portal", "data")
	if err := os.MkdirAll(portalData, 0o755); err != nil {
		t.Fatal(err)
	}

	cfg := `{"kingdoms":{"` + kingdom + `":{"input":"data/taxonomy.json"}}}`
	if err := os.WriteFile(filepath.Join(portalData, "kingdom-config.json"), []byte(cfg), 0o644); err != nil {
		t.Fatal(err)
	}

	families := ""
	for i, slug := range slugs {
		if i > 0 {
			families += ","
		}
		families += `{"rank":"FAMILY","appSlug":"` + slug + `","children":[]}`
	}
	tax := `{"id":"ROOT","rank":"KINGDOM","children":[{"id":"ORDER","rank":"ORDER","children":[` + families + `]}]}`
	if err := os.WriteFile(filepath.Join(portalData, "taxonomy.json"), []byte(tax), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestFamilyRegistry_RegisteredSlugIsRegistered(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae", "canidae"})

	reg := newFamilyRegistry()
	ok, err := reg.isRegistered(root, "animalia", "felidae")
	if err != nil {
		t.Fatal(err)
	}
	if !ok {
		t.Fatalf("expected felidae to be registered")
	}
}

func TestFamilyRegistry_UnregisteredSlugIsNotRegistered(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})

	reg := newFamilyRegistry()
	ok, err := reg.isRegistered(root, "animalia", "nosuchidae")
	if err != nil {
		t.Fatal(err)
	}
	if ok {
		t.Fatalf("expected nosuchidae to NOT be registered")
	}
}

func TestFamilyRegistry_CachesPerKingdom(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})

	reg := newFamilyRegistry()
	if _, err := reg.isRegistered(root, "animalia", "felidae"); err != nil {
		t.Fatal(err)
	}

	// Removing the config entirely after the first lookup must not break a
	// second lookup for the same kingdom -- it should be served from the
	// in-memory cache built on the first call, not re-read from disk.
	if err := os.Remove(filepath.Join(root, "portal", "data", "kingdom-config.json")); err != nil {
		t.Fatal(err)
	}
	ok, err := reg.isRegistered(root, "animalia", "felidae")
	if err != nil {
		t.Fatalf("expected the cached result to be used, got error: %v", err)
	}
	if !ok {
		t.Fatalf("expected felidae to still be registered from cache")
	}
}

func TestLoadFamily_UnregisteredSlugIsRefusedNotCreated(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})
	reg := newFamilyRegistry()

	loc := familyLocation{Kingdom: "animalia", Order: "order", Slug: "nosuchidae"}
	_, err := loadFamily(root, loc, reg)
	if err == nil {
		t.Fatalf("expected loadFamily to refuse an unregistered slug")
	}
	var unreg *unregisteredFamilyError
	if !errors.As(err, &unreg) {
		t.Fatalf("expected an *unregisteredFamilyError, got %T: %v", err, err)
	}
	if unreg.Kingdom != "animalia" || unreg.Slug != "nosuchidae" {
		t.Fatalf("unexpected error fields: %+v", unreg)
	}

	file, existed := resolveFamilyFile(root, loc)
	if existed {
		t.Fatalf("expected no file to have been created at %s", file)
	}
}

func TestLoadFamily_RegisteredButMissingFileStillAutoCreates(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})
	reg := newFamilyRegistry()

	loc := familyLocation{Kingdom: "animalia", Order: "order", Slug: "felidae"}
	fs, err := loadFamily(root, loc, reg)
	if err != nil {
		t.Fatalf("expected a registered-but-not-yet-written family to auto-create, got error: %v", err)
	}
	if fs.root.str("rank") != "FAMILY" {
		t.Fatalf("expected a fresh FAMILY root node, got %+v", fs.root)
	}
}

func TestLoadFamily_NilRegistrySkipsTheCheck(t *testing.T) {
	// Every existing test relies on this: nil means "don't check" (the real
	// store.go call site is the only one that passes a non-nil registry).
	root := t.TempDir()
	loc := familyLocation{Kingdom: "animalia", Order: "order", Slug: "nosuchidae"}
	fs, err := loadFamily(root, loc, nil)
	if err != nil {
		t.Fatalf("expected loadFamily with a nil registry to auto-create unconditionally, got: %v", err)
	}
	if fs.root.str("rank") != "FAMILY" {
		t.Fatalf("expected a fresh FAMILY root node, got %+v", fs.root)
	}
}
