package runproc

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"syscall"
	"testing"
	"time"
)

// A timeout kills grandchildren too, not just the direct child.
func TestRun_TimeoutKillsProcessGroup(t *testing.T) {
	pidFile := filepath.Join(t.TempDir(), "pid")
	_, _, err := Run(context.Background(), 500*time.Millisecond, nil,
		"sh", "-c", "sleep 30 & echo $! > "+pidFile+"; wait")
	if !errors.Is(err, ErrTimeout) {
		t.Fatalf("err = %v, want ErrTimeout", err)
	}
	b, err := os.ReadFile(pidFile)
	if err != nil {
		t.Fatal(err)
	}
	pid, _ := strconv.Atoi(string(b[:len(b)-1]))
	time.Sleep(200 * time.Millisecond)
	if syscall.Kill(pid, 0) == nil {
		syscall.Kill(pid, syscall.SIGKILL)
		t.Fatalf("grandchild %d survived the timeout", pid)
	}
}
