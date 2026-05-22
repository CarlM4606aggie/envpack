"""Tests for envpack.snapshot.SnapshotManager."""

import pytest
from pathlib import Path

from envpack.snapshot import SnapshotManager
from envpack.store import GitStore


ENV_CONTENT = b"DB_HOST=localhost\nDB_PASS=secret\nDEBUG=true\n"
PASSWORD = "hunter2"


@pytest.fixture
def manager(tmp_path: Path) -> SnapshotManager:
    store = GitStore(store_dir=tmp_path / "store")
    store.init()
    return SnapshotManager(store=store)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_bytes(ENV_CONTENT)
    return p


def test_push_creates_snapshot(manager: SnapshotManager, env_file: Path) -> None:
    manager.push(env_file, "prod", PASSWORD)
    assert "prod" in manager.list_snapshots()


def test_pull_restores_original_content(
    manager: SnapshotManager, env_file: Path, tmp_path: Path
) -> None:
    manager.push(env_file, "prod", PASSWORD)
    dest = tmp_path / "restored" / ".env"
    manager.pull("prod", PASSWORD, dest)
    assert dest.read_bytes() == ENV_CONTENT


def test_pull_creates_parent_directories(
    manager: SnapshotManager, env_file: Path, tmp_path: Path
) -> None:
    manager.push(env_file, "prod", PASSWORD)
    dest = tmp_path / "deep" / "nested" / ".env"
    manager.pull("prod", PASSWORD, dest)
    assert dest.exists()


def test_wrong_password_raises_on_pull(
    manager: SnapshotManager, env_file: Path, tmp_path: Path
) -> None:
    manager.push(env_file, "prod", PASSWORD)
    with pytest.raises(Exception):
        manager.pull("prod", "wrongpassword", tmp_path / ".env")


def test_push_missing_file_raises(manager: SnapshotManager, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        manager.push(tmp_path / "nonexistent.env", "prod", PASSWORD)


def test_delete_removes_snapshot(
    manager: SnapshotManager, env_file: Path
) -> None:
    manager.push(env_file, "staging", PASSWORD)
    manager.delete("staging")
    assert "staging" not in manager.list_snapshots()


def test_list_returns_all_snapshots(
    manager: SnapshotManager, env_file: Path
) -> None:
    manager.push(env_file, "dev", PASSWORD)
    manager.push(env_file, "prod", PASSWORD)
    names = manager.list_snapshots()
    assert set(names) >= {"dev", "prod"}
