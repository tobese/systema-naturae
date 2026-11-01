package maintlock

import (
	"os"
	"path/filepath"
	"strconv"
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

func TestSessionWaiting(t *testing.T) {
	dir := t.TempDir()
	if SessionWaiting(dir) {
		t.Fatal("waiting with no marker")
	}
	live := filepath.Join(dir, WaitingPrefix+strconv.Itoa(os.Getpid()))
	os.WriteFile(live, nil, 0644)
	if !SessionWaiting(dir) {
		t.Fatal("live waiter not seen")
	}
	os.Remove(live)
	// A pid far above any real one: the marker of a waiter that died.
	dead := filepath.Join(dir, WaitingPrefix+"99999999")
	os.WriteFile(dead, nil, 0644)
	if SessionWaiting(dir) {
		t.Fatal("dead waiter counted")
	}
	if _, err := os.Stat(dead); !os.IsNotExist(err) {
		t.Fatal("dead waiter's marker not removed")
	}
}
