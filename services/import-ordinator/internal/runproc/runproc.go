// Package runproc runs a pipeline script with a hard deadline and keeps its
// output, so the caller can both log it and parse the numbers it prints.
package runproc

import (
	"bytes"
	"context"
	"errors"
	"io"
	"os"
	"os/exec"
	"time"
)

// ErrTimeout is returned when the script outlived its deadline and was killed.
var ErrTimeout = errors.New("timed out")

// Run executes name+args with env appended to the environment. Output
// (stdout and stderr) is echoed to this process's stdout as it arrives and
// returned whole. rc is the exit code, or -1 if the process never ran or was
// killed for running past timeout (err is then ErrTimeout).
func Run(ctx context.Context, timeout time.Duration, env []string, name string, args ...string) (rc int, out string, err error) {
	if timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}
	cmd := exec.CommandContext(ctx, name, args...)
	cmd.Env = append(os.Environ(), env...)
	var buf bytes.Buffer
	w := io.MultiWriter(os.Stdout, &buf)
	cmd.Stdout = w
	cmd.Stderr = w
	// Kill the child if it ignores the context's kill for this long.
	cmd.WaitDelay = 30 * time.Second

	runErr := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return -1, buf.String(), ErrTimeout
	}
	if runErr != nil {
		var exitErr *exec.ExitError
		if errors.As(runErr, &exitErr) {
			return exitErr.ExitCode(), buf.String(), nil
		}
		return -1, buf.String(), runErr
	}
	return 0, buf.String(), nil
}
