// Package maintlock takes the same lock as scripts/maintenanceLock.py:
// flock(2) on data/.maintenance.lock. Python's fcntl.flock and
// syscall.Flock are the same BSD lock, so the two sides exclude each other.
package maintlock

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

// Lock is a held maintenance lock.
type Lock struct{ f *os.File }

// HoldFile is the file next to the lock that keeps the pipeline out after the
// lock itself is released: scripts/maintenanceSession.py leaves it when a
// maintenance run made an invariant worse, so nothing writes on top of a tree
// no one has checked yet. Same name as maintenanceLock.HOLD_PATH.
const HoldFile = ".maintenance.hold"

// TryAcquire takes the lock without blocking. ok is false if another
// process (a maintenance pass) holds it, or while a maintenance hold is in
// place.
func TryAcquire(path string) (l *Lock, ok bool, err error) {
	if _, err := os.Stat(filepath.Join(filepath.Dir(path), HoldFile)); err == nil {
		return nil, false, nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return nil, false, err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return nil, false, err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		f.Close()
		if errors.Is(err, syscall.EWOULDBLOCK) {
			return nil, false, nil
		}
		return nil, false, err
	}
	return &Lock{f: f}, true, nil
}

// Release drops the lock.
func (l *Lock) Release() {
	syscall.Flock(int(l.f.Fd()), syscall.LOCK_UN)
	l.f.Close()
}

// WaitingPrefix names the marker a maintenance pass blocked on the lock
// leaves while it waits (data/.maintenance.waiting.<pid>); same name as
// maintenanceLock.WAITING_PREFIX. The drain holds the lock for a whole pass,
// so it checks this between sources and ends the pass early.
const WaitingPrefix = ".maintenance.waiting."

// SessionWaiting reports whether a live maintenance pass is waiting for the
// lock in dir. Markers whose process is gone are removed.
func SessionWaiting(dir string) bool {
	matches, _ := filepath.Glob(filepath.Join(dir, WaitingPrefix+"*"))
	waiting := false
	for _, m := range matches {
		var pid int
		if _, err := fmt.Sscanf(filepath.Base(m)[len(WaitingPrefix):], "%d", &pid); err != nil || pid <= 1 {
			continue
		}
		if err := syscall.Kill(pid, 0); err != nil && errors.Is(err, syscall.ESRCH) {
			os.Remove(m)
			continue
		}
		waiting = true
	}
	return waiting
}
