package maintlock

import (
	"os"
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

func TestHoldFileRefusesWithLockFree(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, ".maintenance.lock")
	hold := filepath.Join(dir, HoldFile)
	if err := os.WriteFile(hold, []byte("{}"), 0644); err != nil {
		t.Fatal(err)
	}
	if _, ok, err := TryAcquire(p); ok || err != nil {
		t.Fatalf("acquired while held: ok=%v err=%v", ok, err)
	}
	os.Remove(hold)
	l, ok, err := TryAcquire(p)
	if !ok || err != nil {
		t.Fatalf("not acquirable after the hold was cleared: ok=%v err=%v", ok, err)
	}
	l.Release()
}
