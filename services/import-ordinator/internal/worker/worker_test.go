package worker

import (
	"strings"
	"testing"
)

func TestParseTriaged(t *testing.T) {
	out := "  accepted species/subspecies offered: 4,305\n\n  already held (skipped): 1,298\n  staged:              2,000\n  REFUSED (would need a new family): 1,007 (23.4%)\n"
	tr := parseTriaged(out)
	if tr.Offered == nil || *tr.Offered != 4305 || *tr.AlreadyHeld != 1298 || *tr.Staged != 2000 || *tr.Refused != 1007 {
		t.Fatalf("bad parse: %+v", tr)
	}
	if tr.RefusalRate == nil || *tr.RefusalRate != 0.2339 {
		t.Fatalf("bad refusal rate: %v", *tr.RefusalRate)
	}
	if parseTriaged("nothing").Offered != nil {
		t.Fatal("missing number must stay nil, not zero")
	}
}

func TestParseApplied(t *testing.T) {
	out := "  importwrite: 179 added, 1419 merged (2 already existed in a different family)\n  flushed 515 families\n"
	a, m, c, f := parseApplied(out)
	if a != 179 || m != 1419 || c != 2 || f != 515 {
		t.Fatalf("got %d %d %d %d", a, m, c, f)
	}
}

func TestNCLicence(t *testing.T) {
	for lic, want := range map[string]bool{"CC BY-NC 4.0": true, "cc by nc": true, "cc by": false, "cc0": false, "unknown licence": false} {
		got := ncLicence.MatchString(licenceSep.ReplaceAllString(strings.ToLower(lic), " "))
		if got != want {
			t.Errorf("%q: got %v want %v", lic, got, want)
		}
	}
}
