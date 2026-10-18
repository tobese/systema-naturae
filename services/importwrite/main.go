// Command importwrite is the single writer for taxonomy family JSON files.
//
// Importers that currently write taxonomy/<kingdom>/.../<family>/src/data/
// <family>.json directly and commit from whichever machine ran them (Macie,
// Steamie, Debbie, q-bert) instead POST their species nodes here. One
// process serializes writes per family and owns the merge/dedupe decision,
// so two importers adding the same species no longer produce two copies for
// a later git merge to union together.
//
// See README.md for the API, the identity/merge rules, and what this POC
// deliberately does not yet handle.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

func main() {
	root := envOr("IMPORTWRITE_ROOT", "../..")
	port := envOr("IMPORTWRITE_PORT", "8089")
	gitCommit := envOr("IMPORTWRITE_GIT_COMMIT", "0") == "1"
	flushInterval := durationEnv("IMPORTWRITE_FLUSH_INTERVAL", 5*time.Second)
	idleEvict := durationEnv("IMPORTWRITE_IDLE_EVICT", 10*time.Minute)

	absRoot, err := filepath.Abs(root)
	if err != nil {
		log.Fatalf("resolving root %q: %v", root, err)
	}
	log.Printf("importwrite: repo root %s, git commit %v, flush every %s", absRoot, gitCommit, flushInterval)

	st := newStore(absRoot, gitCommit, idleEvict)
	go st.flushLoop(flushInterval)

	mux := http.NewServeMux()
	mux.HandleFunc("POST /family/{slug}/species", handleImport(st))
	mux.HandleFunc("GET /family/{slug}", handleGet(st))
	mux.HandleFunc("POST /family/{slug}/flush", handleFlushOne(st))
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	addr := ":" + port
	log.Printf("importwrite: listening on %s", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}

func handleImport(st *store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req importRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad request body: "+err.Error(), http.StatusBadRequest)
			return
		}
		slug := r.PathValue("slug")
		if req.Kingdom == "" {
			http.Error(w, "kingdom is required", http.StatusBadRequest)
			return
		}
		loc := familyLocation{Kingdom: req.Kingdom, Phylum: req.Phylum, Class: req.Class, Order: req.Order, Slug: slug}
		fs, err := st.get(loc)
		if err != nil {
			http.Error(w, "loading family: "+err.Error(), http.StatusInternalServerError)
			return
		}
		result := fs.apply(req)
		writeJSON(w, http.StatusOK, result)
	}
}

func handleGet(st *store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		slug := r.PathValue("slug")
		kingdom := r.URL.Query().Get("kingdom")
		if kingdom == "" {
			http.Error(w, "kingdom query param is required", http.StatusBadRequest)
			return
		}
		loc := familyLocation{
			Kingdom: kingdom,
			Phylum:  r.URL.Query().Get("phylum"),
			Class:   r.URL.Query().Get("class"),
			Order:   r.URL.Query().Get("order"),
			Slug:    slug,
		}
		fs, err := st.get(loc)
		if err != nil {
			http.Error(w, "loading family: "+err.Error(), http.StatusInternalServerError)
			return
		}
		fs.mu.Lock()
		defer fs.mu.Unlock()
		writeJSON(w, http.StatusOK, fs.root)
	}
}

func handleFlushOne(st *store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		slug := r.PathValue("slug")
		st.mu.Lock()
		fs, ok := st.families[slug]
		st.mu.Unlock()
		if !ok {
			http.Error(w, "family not loaded: "+slug, http.StatusNotFound)
			return
		}
		wrote, err := fs.flush()
		if err != nil {
			http.Error(w, "flush: "+err.Error(), http.StatusInternalServerError)
			return
		}
		if wrote && st.gitCommit {
			if err := commitFamily(st.root, fs.slug, fs.file); err != nil {
				http.Error(w, "git commit: "+err.Error(), http.StatusInternalServerError)
				return
			}
		}
		writeJSON(w, http.StatusOK, map[string]any{"wrote": wrote})
	}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func durationEnv(key string, fallback time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	if secs, err := strconv.Atoi(v); err == nil {
		return time.Duration(secs) * time.Second
	}
	if d, err := time.ParseDuration(v); err == nil {
		return d
	}
	return fallback
}
