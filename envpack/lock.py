"""Lock file management to prevent concurrent envpack operations."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional


class LockError(Exception):
    """Raised when a lock cannot be acquired or is invalid."""


LOCK_FILENAME = ".envpack.lock"
DEFAULT_TIMEOUT = 10.0  # seconds
STALE_AFTER = 60.0  # seconds before a lock is considered stale


class StoreLock:
    """File-based lock for a store directory."""

    def __init__(self, store_path: Path, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.lock_path = store_path / LOCK_FILENAME
        self.timeout = timeout
        self._acquired = False

    def acquire(self) -> None:
        """Attempt to acquire the lock, blocking up to *timeout* seconds."""
        deadline = time.monotonic() + self.timeout
        while True:
            self._clear_stale()
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as fh:
                    fh.write(f"{os.getpid()}\n{time.time()}\n")
                self._acquired = True
                return
            except FileExistsError:
                if time.monotonic() >= deadline:
                    owner = self._read_pid()
                    raise LockError(
                        f"Could not acquire lock at {self.lock_path} "
                        f"(held by PID {owner}). Is another envpack process running?"
                    )
                time.sleep(0.1)

    def release(self) -> None:
        """Release the lock if we hold it."""
        if self._acquired and self.lock_path.exists():
            self.lock_path.unlink(missing_ok=True)
            self._acquired = False

    def _clear_stale(self) -> None:
        """Remove the lock file if it is older than STALE_AFTER seconds."""
        try:
            mtime = self.lock_path.stat().st_mtime
            if time.time() - mtime > STALE_AFTER:
                self.lock_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass

    def _read_pid(self) -> Optional[int]:
        try:
            lines = self.lock_path.read_text().splitlines()
            return int(lines[0]) if lines else None
        except Exception:
            return None

    def __enter__(self) -> "StoreLock":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
