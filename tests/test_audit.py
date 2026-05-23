"""Tests for envpack.audit."""
import pytest
from pathlib import Path
from envpack.audit import AuditEntry, AuditLog


@pytest.fixture
def log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path)


def test_record_creates_file(log: AuditLog, tmp_path: Path) -> None:
    entry = AuditEntry.now("push", "default", "my-app", ".env")
    log.record(entry)
    assert (tmp_path / "audit.log").exists()


def test_entries_empty_when_no_log(log: AuditLog) -> None:
    assert log.entries() == []


def test_round_trip_single_entry(log: AuditLog) -> None:
    entry = AuditEntry.now("pull", "prod", "api-service", "/home/user/.env", note="restore")
    log.record(entry)
    entries = log.entries()
    assert len(entries) == 1
    e = entries[0]
    assert e.action == "pull"
    assert e.profile == "prod"
    assert e.snapshot_name == "api-service"
    assert e.env_path == "/home/user/.env"
    assert e.note == "restore"


def test_entries_are_returned_newest_first(log: AuditLog) -> None:
    for i in range(3):
        log.record(AuditEntry.now("push", "default", f"snap-{i}", ".env"))
    entries = log.entries()
    names = [e.snapshot_name for e in entries]
    assert names == ["snap-2", "snap-1", "snap-0"]


def test_limit_parameter(log: AuditLog) -> None:
    for i in range(5):
        log.record(AuditEntry.now("push", "default", f"snap-{i}", ".env"))
    assert len(log.entries(limit=2)) == 2


def test_clear_removes_log(log: AuditLog, tmp_path: Path) -> None:
    log.record(AuditEntry.now("push", "default", "snap", ".env"))
    log.clear()
    assert not (tmp_path / "audit.log").exists()
    assert log.entries() == []


def test_entry_has_timestamp(log: AuditLog) -> None:
    entry = AuditEntry.now("push", "default", "snap", ".env")
    assert entry.timestamp.endswith("+00:00")


def test_to_and_from_json_roundtrip() -> None:
    entry = AuditEntry.now("push", "staging", "my-snap", ".env", note="test")
    restored = AuditEntry.from_json(entry.to_json())
    assert restored == entry
