package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

// bacteriaVirusesInput mirrors importColChecklist.py's BACTERIA_VIRUSES_INPUT:
// the two kingdoms are imported but deliberately absent from
// kingdom-config.json, which is the build side's list (portal stays six).
var bacteriaVirusesInput = map[string]string{
	"bacteria": "data/taxonomy-bacteria.json",
	"viruses":  "data/taxonomy-viruses.json",
}

// writerPartition is the set of kingdoms this importwrite may write, the Go
// side of scripts/writerKingdoms.py: SN_WRITE_KINGDOMS (comma-separated), or
// when unset the kingdoms in kingdom-config.json. Decided 2026-10-30: q-bert
// writes bacteria and viruses, Macie the six portal kingdoms; mixed sources
// (NCBI, ENA, Wikidata, COL XR, the Backbone) are applied on both, and each
// writer has to refuse the other's kingdoms rather than trust every caller to
// filter.
type writerPartition struct {
	once    sync.Once
	allowed map[string]bool
	err     error
}

func (p *writerPartition) load(root string) {
	p.allowed = map[string]bool{}
	if raw := strings.TrimSpace(os.Getenv("SN_WRITE_KINGDOMS")); raw != "" {
		for _, k := range strings.Split(raw, ",") {
			if k = strings.ToLower(strings.TrimSpace(k)); k != "" {
				p.allowed[k] = true
			}
		}
		return
	}
	cfgPath := filepath.Join(root, "portal", "data", "kingdom-config.json")
	raw, err := os.ReadFile(cfgPath)
	if err != nil {
		p.err = fmt.Errorf("reading %s: %w", cfgPath, err)
		return
	}
	var cfg kingdomConfig
	if err := json.Unmarshal(raw, &cfg); err != nil {
		p.err = fmt.Errorf("parsing %s: %w", cfgPath, err)
		return
	}
	for k := range cfg.Kingdoms {
		p.allowed[k] = true
	}
}

// mayWrite reports whether kingdom belongs to this writer.
func (p *writerPartition) mayWrite(root, kingdom string) (bool, error) {
	p.once.Do(func() { p.load(root) })
	if p.err != nil {
		return false, p.err
	}
	return p.allowed[strings.ToLower(kingdom)], nil
}

func (p *writerPartition) list() string {
	ks := make([]string, 0, len(p.allowed))
	for k := range p.allowed {
		ks = append(ks, k)
	}
	sort.Strings(ks)
	return strings.Join(ks, ",")
}
