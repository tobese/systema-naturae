// Package maintlock takes the same lock as scripts/maintenanceLock.py:
// flock(2) on data/.maintenance.lock. Python's fcntl.flock and
// syscall.Flock are the same BSD lock, so the two sides exclude each other.
package maintlock

import (
	"errors"
	"os"
	"path/filepath"
	"syscall"
)

// Lock is a held maintenance lock.
type Lock struct{ f *os.File }

// TryAcquire takes the lock without blocking. ok is false if another
// process (a maintenance pass) holds it.
func TryAcquire(path string) (l *Lock, ok bool, err error) {
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
