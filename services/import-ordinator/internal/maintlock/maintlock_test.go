package maintlock

import (
	"path/filepath"
	"testing"
)

func TestSecondHolderIsRefused(t *testing.T) {
	p := filepath.Join(t.TempDir(), ".maintenance.lock")
	a, ok, err := TryAcquire(p)
	if err != nil || !ok {
		t.Fatalf("first acquire: ok=%v err=%v", ok, err)
	}
	if _, ok, _ := TryAcquire(p); ok {
		t.Fatal("second descriptor got the lock while it was held")
	}
	a.Release()
	b, ok, _ := TryAcquire(p)
	if !ok {
		t.Fatal("lock not reacquirable after release")
	}
	b.Release()
}
