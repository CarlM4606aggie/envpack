"""Tests for envpack.remind."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from envpack.remind import (
    RemindError,
    ReminderEntry,
    ReminderReport,
    check_staleness,
)
from envpack.store import GitStore


@pytest.fixture()
def store(tmp_path: Path) -> GitStore:
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, content: bytes = b"KEY=val") -> None:
    store.save(name, content)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# ReminderEntry
# ---------------------------------------------------------------------------

def test_reminder_entry_str_contains_name():
    entry = ReminderEntry(name="prod", last_modified=_now(), age_days=5.0, threshold_days=30)
    assert "prod" in str(entry)


def test_reminder_entry_str_contains_age():
    entry = ReminderEntry(name="prod", last_modified=_now(), age_days=12.3, threshold_days=30)
    assert "12.3" in str(entry)


# ---------------------------------------------------------------------------
# ReminderReport
# ---------------------------------------------------------------------------

def test_report_stale_filters_correctly():
    now = _now()
    entries = [
        ReminderEntry("a", now, age_days=5.0, threshold_days=30),
        ReminderEntry("b", now, age_days=40.0, threshold_days=30),
    ]
    report = ReminderReport(entries=entries, threshold_days=30)
    assert len(report.stale) == 1
    assert report.stale[0].name == "b"


def test_report_ok_filters_correctly():
    now = _now()
    entries = [
        ReminderEntry("a", now, age_days=5.0, threshold_days=30),
        ReminderEntry("b", now, age_days=40.0, threshold_days=30),
    ]
    report = ReminderReport(entries=entries, threshold_days=30)
    assert len(report.ok) == 1
    assert report.ok[0].name == "a"


def test_report_summary_empty():
    report = ReminderReport(entries=[], threshold_days=30)
    assert "No snapshots" in report.summary()


def test_report_summary_all_ok():
    now = _now()
    entries = [ReminderEntry("a", now, age_days=1.0, threshold_days=30)]
    report = ReminderReport(entries=entries, threshold_days=30)
    assert "up to date" in report.summary()


def test_report_summary_stale_mentions_name():
    now = _now()
    entries = [ReminderEntry("prod", now, age_days=60.0, threshold_days=30)]
    report = ReminderReport(entries=entries, threshold_days=30)
    assert "prod" in report.summary()


# ---------------------------------------------------------------------------
# check_staleness
# ---------------------------------------------------------------------------

def test_invalid_threshold_raises(store: GitStore):
    with pytest.raises(RemindError):
        check_staleness(store, threshold_days=0)


def test_empty_store_returns_empty_report(store: GitStore):
    report = check_staleness(store, threshold_days=30)
    assert report.entries == []


def test_fresh_snapshot_not_stale(store: GitStore):
    _seed(store, "fresh")
    report = check_staleness(store, threshold_days=30)
    assert all(e.age_days < 30 for e in report.entries)
    assert report.stale == []


def test_old_snapshot_is_stale(store: GitStore):
    _seed(store, "old")
    future_now = _now() + timedelta(days=45)
    with patch("envpack.remind.datetime") as mock_dt:
        mock_dt.now.return_value = future_now
        report = check_staleness(store, threshold_days=30)
    assert len(report.stale) == 1
    assert report.stale[0].name == "old"


def test_entries_sorted_by_age_descending(store: GitStore):
    _seed(store, "alpha")
    _seed(store, "beta")
    future_now = _now() + timedelta(days=10)
    with patch("envpack.remind.datetime") as mock_dt:
        mock_dt.now.return_value = future_now
        report = check_staleness(store, threshold_days=30)
    ages = [e.age_days for e in report.entries]
    assert ages == sorted(ages, reverse=True)
