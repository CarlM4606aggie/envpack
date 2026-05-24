"""Tests for envpack.rename."""
from __future__ import annotations

import pytest

from envpack.crypto import encrypt
from envpack.rename import RenameError, RenameResult, rename_snapshot
from envpack.store import GitStore


PASSWORD = "s3cr3t"
PLAINTEXT = b"DB_HOST=localhost\nDB_PORT=5432\n"


@pytest.fixture()
def store(tmp_path):
    s = GitStore(str(tmp_path / "store"))
    s.init()
    return s


def _seed(store: GitStore, name: str) -> None:
    store.save(name, encrypt(PLAINTEXT, PASSWORD))


def test_rename_returns_result(store):
    _seed(store, "alpha")
    result = rename_snapshot(store, "alpha", "beta", PASSWORD)
    assert isinstance(result, RenameResult)
    assert result.old_name == "alpha"
    assert result.new_name == "beta"


def test_rename_new_name_appears_in_list(store):
    _seed(store, "alpha")
    rename_snapshot(store, "alpha", "beta", PASSWORD)
    assert "beta" in store.list()


def test_rename_old_name_removed_from_list(store):
    _seed(store, "alpha")
    rename_snapshot(store, "alpha", "beta", PASSWORD)
    assert "alpha" not in store.list()


def test_rename_data_intact_after_rename(store):
    from envpack.crypto import decrypt

    _seed(store, "alpha")
    rename_snapshot(store, "alpha", "beta", PASSWORD)
    raw = store.load("beta")
    assert decrypt(raw, PASSWORD) == PLAINTEXT


def test_rename_identical_names_raises(store):
    _seed(store, "alpha")
    with pytest.raises(RenameError, match="identical"):
        rename_snapshot(store, "alpha", "alpha", PASSWORD)


def test_rename_missing_old_name_raises(store):
    with pytest.raises(RenameError, match="not found"):
        rename_snapshot(store, "ghost", "new", PASSWORD)


def test_rename_existing_new_name_raises(store):
    _seed(store, "alpha")
    _seed(store, "beta")
    with pytest.raises(RenameError, match="already exists"):
        rename_snapshot(store, "alpha", "beta", PASSWORD)


def test_summary_contains_both_names(store):
    _seed(store, "alpha")
    result = rename_snapshot(store, "alpha", "beta", PASSWORD)
    summary = result.summary()
    assert "alpha" in summary
    assert "beta" in summary
