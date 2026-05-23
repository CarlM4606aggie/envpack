"""Tests for envpack.restore."""

from __future__ import annotations

from pathlib import Path

import pytest

from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.restore import restore_snapshot, RestoreError


PASSWORD = "hunter2"
CONTENT = b"API_KEY=secret\nDEBUG=true\n"


@pytest.fixture()
def store(tmp_path: Path) -> GitStore:
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, content: bytes = CONTENT) -> None:
    store.save(name, encrypt(content, PASSWORD))


def test_restore_writes_decrypted_content(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / "out" / ".env"
    result = restore_snapshot(store, "prod", PASSWORD, target)
    assert target.read_bytes() == CONTENT
    assert result.snapshot_name == "prod"
    assert result.target == target.resolve()


def test_restore_creates_parent_directories(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / "deep" / "nested" / "dir" / ".env"
    restore_snapshot(store, "prod", PASSWORD, target)
    assert target.exists()


def test_restore_creates_backup_when_target_exists(
    store: GitStore, tmp_path: Path
) -> None:
    _seed(store, "prod")
    target = tmp_path / ".env"
    target.write_text("OLD=value\n")

    result = restore_snapshot(store, "prod", PASSWORD, target)

    assert result.overwrote_existing is True
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.backup_path.read_text() == "OLD=value\n"
    assert target.read_bytes() == CONTENT


def test_restore_no_backup_skips_backup(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / ".env"
    target.write_text("OLD=value\n")

    result = restore_snapshot(store, "prod", PASSWORD, target, backup=False)

    assert result.backup_path is None
    assert target.read_bytes() == CONTENT


def test_restore_missing_snapshot_raises(store: GitStore, tmp_path: Path) -> None:
    with pytest.raises(RestoreError, match="Snapshot not found"):
        restore_snapshot(store, "nonexistent", PASSWORD, tmp_path / ".env")


def test_restore_wrong_password_raises(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    with pytest.raises(RestoreError, match="Decryption failed"):
        restore_snapshot(store, "prod", "wrongpassword", tmp_path / ".env")


def test_summary_contains_snapshot_name(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "staging")
    result = restore_snapshot(store, "staging", PASSWORD, tmp_path / ".env")
    assert "staging" in result.summary()
