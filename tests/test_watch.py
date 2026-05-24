"""Tests for envpack.watch."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envpack.watch import WatchError, WatchEvent, _file_hash, watch_file


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

def test_file_hash_returns_string_for_existing_file(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    result = _file_hash(f)
    assert isinstance(result, str) and len(result) == 64


def test_file_hash_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _file_hash(tmp_path / "missing.env") is None


def test_file_hash_changes_when_content_changes(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("A=1")
    h1 = _file_hash(f)
    f.write_text("A=2")
    h2 = _file_hash(f)
    assert h1 != h2


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_is_first_seen_when_old_hash_none() -> None:
    event = WatchEvent(path=Path(".env"), old_hash=None, new_hash="abc")
    assert event.is_first_seen is True


def test_watch_event_not_first_seen_when_old_hash_present() -> None:
    event = WatchEvent(path=Path(".env"), old_hash="old", new_hash="new")
    assert event.is_first_seen is False


# ---------------------------------------------------------------------------
# watch_file
# ---------------------------------------------------------------------------

def test_watch_file_detects_change(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=1")

    events: list[WatchEvent] = []

    def write_and_collect(event: WatchEvent) -> None:
        events.append(event)

    # Patch sleep so the test doesn't actually wait
    import envpack.watch as watch_mod
    original_sleep = time.sleep
    calls = [0]

    def fast_sleep(secs: float) -> None:  # noqa: ARG001
        calls[0] += 1
        if calls[0] == 1:
            f.write_text("KEY=2")  # trigger change on first iteration

    watch_mod.time.sleep = fast_sleep  # type: ignore[attr-defined]
    try:
        watch_file(f, write_and_collect, interval=0.01, max_iterations=2)
    finally:
        watch_mod.time.sleep = original_sleep  # type: ignore[attr-defined]

    assert len(events) == 1
    assert events[0].new_hash != events[0].old_hash


def test_watch_file_raises_when_directory_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent" / ".env"
    with pytest.raises(WatchError, match="Directory does not exist"):
        watch_file(missing, lambda e: None, interval=0.01, max_iterations=1)


def test_watch_file_no_event_when_file_unchanged(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("STABLE=yes")

    events: list[WatchEvent] = []
    import envpack.watch as watch_mod
    watch_mod.time.sleep = lambda _: None  # type: ignore[attr-defined]
    try:
        watch_file(f, events.append, interval=0.01, max_iterations=3)
    finally:
        import importlib, envpack.watch  # noqa: E401
        importlib.reload(envpack.watch)

    assert events == []
