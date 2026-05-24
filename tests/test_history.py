"""Tests for envpack.history."""
from __future__ import annotations

import pytest

from envpack.history import HistoryEntry, HistoryReport, HistoryError, get_history
from envpack.store import GitStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, names: list[str]) -> None:
    for name in names:
        store.save(name, f"KEY={name}\n".encode())


# ---------------------------------------------------------------------------
# HistoryEntry / HistoryReport unit tests
# ---------------------------------------------------------------------------

def test_history_entry_str():
    entry = HistoryEntry(name="snap-001", index=0, size_bytes=128)
    assert "snap-001" in str(entry)
    assert "128" in str(entry)
    assert "[0]" in str(entry)


def test_history_report_summary_empty():
    report = HistoryReport(entries=[])
    assert "No snapshots" in report.summary()


def test_history_report_total():
    entries = [
        HistoryEntry(name="a", index=0, size_bytes=10),
        HistoryEntry(name="b", index=1, size_bytes=20),
    ]
    report = HistoryReport(entries=entries)
    assert report.total == 2


def test_history_report_summary_lists_names():
    entries = [
        HistoryEntry(name="snap-b", index=0, size_bytes=50),
        HistoryEntry(name="snap-a", index=1, size_bytes=30),
    ]
    summary = HistoryReport(entries=entries).summary()
    assert "snap-b" in summary
    assert "snap-a" in summary


# ---------------------------------------------------------------------------
# get_history integration tests
# ---------------------------------------------------------------------------

def test_get_history_empty_store(store):
    report = get_history(store)
    assert report.total == 0


def test_get_history_returns_entries(store):
    _seed(store, ["snap-001", "snap-002", "snap-003"])
    report = get_history(store)
    assert report.total == 3


def test_get_history_newest_first(store):
    _seed(store, ["snap-001", "snap-002", "snap-003"])
    report = get_history(store)
    names = [e.name for e in report.entries]
    assert names == sorted(names, reverse=True)


def test_get_history_limit(store):
    _seed(store, ["snap-001", "snap-002", "snap-003", "snap-004"])
    report = get_history(store, limit=2)
    assert report.total == 2


def test_get_history_entries_have_positive_size(store):
    _seed(store, ["snap-x"])
    report = get_history(store)
    assert report.entries[0].size_bytes > 0


def test_get_history_index_starts_at_zero(store):
    _seed(store, ["snap-a", "snap-b"])
    report = get_history(store)
    assert report.entries[0].index == 0
    assert report.entries[1].index == 1
