"""Tests for envpack.rollback."""
from __future__ import annotations

from pathlib import Path

import pytest

from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.rollback import rollback_snapshot, RollbackError

PASSWORD = "s3cr3t"
CONTENT = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def store(tmp_path: Path) -> GitStore:
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, content: bytes = CONTENT) -> None:
    store.save(name, encrypt(content, PASSWORD))


def test_rollback_writes_decrypted_content(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / "out" / ".env"
    result = rollback_snapshot(store, "prod", PASSWORD, target, backup=False)
    assert target.read_bytes() == CONTENT
    assert result.backup is None


def test_rollback_creates_parent_directories(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / "deep" / "nested" / ".env"
    rollback_snapshot(store, "prod", PASSWORD, target, backup=False)
    assert target.exists()


def test_rollback_creates_backup_when_target_exists(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / ".env"
    target.write_text("OLD=value\n")
    result = rollback_snapshot(store, "prod", PASSWORD, target, backup=True)
    assert result.backup is not None
    assert result.backup.exists()
    assert result.backup.read_text() == "OLD=value\n"
    assert target.read_bytes() == CONTENT


def test_rollback_no_backup_flag_skips_backup(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / ".env"
    target.write_text("OLD=value\n")
    result = rollback_snapshot(store, "prod", PASSWORD, target, backup=False)
    assert result.backup is None


def test_rollback_missing_snapshot_raises(store: GitStore, tmp_path: Path) -> None:
    target = tmp_path / ".env"
    with pytest.raises(RollbackError, match="not found"):
        rollback_snapshot(store, "nonexistent", PASSWORD, target)


def test_rollback_wrong_password_raises(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "prod")
    target = tmp_path / ".env"
    with pytest.raises(RollbackError, match="Decryption failed"):
        rollback_snapshot(store, "prod", "wrong-password", target)


def test_rollback_result_summary(store: GitStore, tmp_path: Path) -> None:
    _seed(store, "staging")
    target = tmp_path / ".env"
    target.write_text("EXISTING=1\n")
    result = rollback_snapshot(store, "staging", PASSWORD, target, backup=True)
    summary = result.summary()
    assert "staging" in summary
    assert str(target) in summary
    assert ".bak" in summary
