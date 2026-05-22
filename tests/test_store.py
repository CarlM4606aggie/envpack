"""Tests for envpack.store.GitStore."""

import pytest
from pathlib import Path

from envpack.store import GitStore, StoreError


@pytest.fixture
def store(tmp_path: Path) -> GitStore:
    s = GitStore(store_dir=tmp_path / "store")
    s.init()
    return s


def test_init_creates_git_repo(tmp_path: Path) -> None:
    s = GitStore(store_dir=tmp_path / "mystore")
    s.init()
    assert (tmp_path / "mystore" / ".git").is_dir()


def test_init_is_idempotent(store: GitStore) -> None:
    store.init()  # second call should not raise


def test_save_and_load_round_trip(store: GitStore) -> None:
    data = b"encrypted-payload-bytes"
    store.save("myapp", data)
    assert store.load("myapp") == data


def test_load_missing_snapshot_raises(store: GitStore) -> None:
    with pytest.raises(StoreError, match="not found"):
        store.load("nonexistent")


def test_list_snapshots_empty(store: GitStore) -> None:
    assert store.list_snapshots() == []


def test_list_snapshots_after_saves(store: GitStore) -> None:
    store.save("alpha", b"aaa")
    store.save("beta", b"bbb")
    names = store.list_snapshots()
    assert "alpha" in names
    assert "beta" in names


def test_delete_removes_snapshot(store: GitStore) -> None:
    store.save("temp", b"data")
    store.delete("temp")
    assert "temp" not in store.list_snapshots()


def test_delete_missing_snapshot_raises(store: GitStore) -> None:
    with pytest.raises(StoreError, match="not found"):
        store.delete("ghost")


def test_operations_without_init_raise(tmp_path: Path) -> None:
    s = GitStore(store_dir=tmp_path / "uninit")
    with pytest.raises(StoreError, match="not initialized"):
        s.save("x", b"data")
    with pytest.raises(StoreError, match="not initialized"):
        s.load("x")
    with pytest.raises(StoreError, match="not initialized"):
        s.list_snapshots()
