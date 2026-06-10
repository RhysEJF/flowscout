#!/usr/bin/env python3
"""
with-lock.py — run a command while holding an exclusive POSIX file lock.

Used to serialize concurrent operations across sub-agents (qmd embed, INDEX.md
append) that aren't safe to run in parallel. Python's `fcntl` ships with the
stdlib on macOS and Linux — no `flock` binary required.

Usage:
    python3 scripts/with-lock.py <lockfile> [--timeout SECS] -- <command> [args...]

Examples:
    python3 scripts/with-lock.py /tmp/qmd-embed.lock -- ./vendor/qmd/bin/qmd embed
    python3 scripts/with-lock.py /tmp/papers-index.lock --timeout 30 -- bash -c 'echo "row" >> INDEX.md'

Exit codes:
    0    command succeeded
    1    lock acquisition timed out
    124  command exit code passed through (after lock was held)
    >0   any other command exit code passed through

The lockfile is created if it doesn't exist; it is never deleted (cheap, and
safe — the lock is on the file descriptor, not the file's existence).
"""
import fcntl
import os
import signal
import subprocess
import sys
import time


def parse_args(argv):
    if len(argv) < 4 or '--' not in argv:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    lockfile = argv[1]
    rest = argv[2:]
    timeout = None
    if rest and rest[0] == '--timeout':
        timeout = int(rest[1])
        rest = rest[2:]
    if not rest or rest[0] != '--':
        print("Expected `--` separator before command. See --help.", file=sys.stderr)
        sys.exit(2)
    cmd = rest[1:]
    if not cmd:
        print("No command provided after `--`.", file=sys.stderr)
        sys.exit(2)
    return lockfile, timeout, cmd


def acquire_lock(lockfile, timeout=None):
    """Open lockfile and acquire exclusive POSIX lock. Return the fd object."""
    # Ensure parent dir exists (lockfile may live in a path the caller assumed)
    parent = os.path.dirname(lockfile)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    f = open(lockfile, 'a+')  # 'a+' creates if missing, doesn't truncate
    if timeout is None:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return f
    # Non-blocking with retry loop for timeout support
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return f
        except BlockingIOError:
            if time.monotonic() >= deadline:
                f.close()
                print(f"with-lock: timed out waiting for {lockfile} after {timeout}s",
                      file=sys.stderr)
                sys.exit(1)
            time.sleep(0.1)


def main():
    lockfile, timeout, cmd = parse_args(sys.argv)
    fd = acquire_lock(lockfile, timeout)
    try:
        # Pass through stdin/stdout/stderr unchanged
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    finally:
        # Lock auto-released when fd closes, but explicit is clearer
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        fd.close()


if __name__ == '__main__':
    main()
