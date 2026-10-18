package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// newTestServer wires a store with a real registry (unlike the rest of the
// package's tests, which pass registry: nil) behind the same mux main()
// builds, so these tests exercise the actual HTTP wiring of the
// unregistered-family refusal, not just loadFamily in isolation.
func newTestServer(t *testing.T, root string) *httptest.Server {
	t.Helper()
	st := newStore(root, false, 0)
	mux := http.NewServeMux()
	mux.HandleFunc("POST /family/{slug}/species", handleImport(st))
	mux.HandleFunc("GET /family/{slug}", handleGet(st))
	srv := httptest.NewServer(mux)
	t.Cleanup(srv.Close)
	return srv
}

func TestHandleImport_UnregisteredFamilyReturns422(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})
	srv := newTestServer(t, root)

	body := strings.NewReader(`{"kingdom":"animalia","genus":{"name":"Nosuchus"},"species":[{"name":"Nosuchus novus"}]}`)
	resp, err := http.Post(srv.URL+"/family/nosuchidae/species", "application/json", body)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnprocessableEntity {
		t.Fatalf("expected 422, got %d", resp.StatusCode)
	}
	var out map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatal(err)
	}
	if out["unregistered"] != true {
		t.Fatalf(`expected "unregistered": true, got %+v`, out)
	}
	if out["family"] != "nosuchidae" || out["kingdom"] != "animalia" {
		t.Fatalf("unexpected kingdom/family fields: %+v", out)
	}
	if out["speciesOffered"] != float64(1) {
		t.Fatalf("expected speciesOffered: 1, got %+v", out["speciesOffered"])
	}
}

func TestHandleImport_RegisteredFamilySucceeds(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})
	srv := newTestServer(t, root)

	body := strings.NewReader(`{"kingdom":"animalia","genus":{"name":"Panthera"},"species":[{"name":"Panthera leo"}]}`)
	resp, err := http.Post(srv.URL+"/family/felidae/species", "application/json", body)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200 for a registered family with no file yet, got %d", resp.StatusCode)
	}
}

func TestHandleGet_UnregisteredFamilyReturns404(t *testing.T) {
	root := t.TempDir()
	writeFixtureKingdomConfig(t, root, "animalia", []string{"felidae"})
	srv := newTestServer(t, root)

	resp, err := http.Get(srv.URL + "/family/nosuchidae?kingdom=animalia")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
}
