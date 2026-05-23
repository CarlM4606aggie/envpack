"""Tests for envpack.lock."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from envpack.lock import LockError, StoreLock, STALE_AFTER


@pytest.fixture()
def store_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_acquire_creates_lock_file(store_dir: Path) -> None:
    lock = StoreLock(store_dir)
    lock.acquire()
    assert (store_dir / ".envpack.lock").exists()
    lock.release()


def test_release_removes_lock_file(store_dir: Path) -> None:
    lock = StoreLock(store_dir)
    lock.acquire()
    lock.release()
    assert not (store_dir / ".envpack.lock").exists()


def test_context_manager_acquires_and_releases(store_dir: Path) -> None:
    with StoreLock(store_dir):
        assert (store_dir / ".envpack.lock").exists()
    assert not (store_dir / ".envpack.lock").exists()


def test_double_acquire_raises_lock_error(store_dir: Path) -> None:
    lock1 = StoreLock(store_dir, timeout=0.2)
    lock2 = StoreLock(store_dir, timeout=0.2)
    lock1.acquire()
    try:
        with pytest.raises(LockError, match="Could not acquire lock"):
            lock2.acquire()
    finally:
        lock1.release()


def test_lock_file_contains_pid(store_dir: Path) -> None:
    import os

    with StoreLock(store_dir):
        content = (store_dir / ".envpack.lock").read_text()
        pid_line = content.splitlines()[0]
        assert int(pid_line) == os.getpid()


def test_stale_lock_is_cleared(store_dir: Path) -> None:
    lock_path = store_dir / ".envpack.lock"
    lock_path.write_text("99999\n0.0\n")
    # backdate mtime so it appears stale
    stale_time = time.time() - STALE_AFTER - 5
    import os
    os.utime(lock_path, (stale_time, stale_time))

    lock = StoreLock(store_dir, timeout=0.5)
    lock.acquire()
    assert lock_path.exists()
    lock.release()


def test_release_without_acquire_is_safe(store_dir: Path) -> None:
    lock = StoreLock(store_dir)
    lock.release()  # should not raise
