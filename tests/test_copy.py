"""Tests for envpack.copy."""
from __future__ import annotations

import pytest

from envpack.copy import CopyError, CopyResult, copy_snapshot
from envpack.store import GitStore


@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, name: str, profile: str = "default", data: bytes = b"DATA") -> None:
    store.save(name, profile, data)


def test_copy_returns_result(store):
    _seed(store, "snap1")
    result = copy_snapshot(store, "snap1", "snap2")
    assert isinstance(result, CopyResult)
    assert result.source == "snap1"
    assert result.destination == "snap2"


def test_copy_destination_appears_in_list(store):
    _seed(store, "snap1")
    copy_snapshot(store, "snap1", "snap2")
    assert "snap2" in store.list("default")


def test_copy_source_still_exists(store):
    _seed(store, "snap1")
    copy_snapshot(store, "snap1", "snap2")
    assert "snap1" in store.list("default")


def test_copy_data_is_identical(store):
    payload = b"encrypted-payload-bytes"
    _seed(store, "snap1", data=payload)
    copy_snapshot(store, "snap1", "snap2")
    assert store.load("snap2", "default") == payload


def test_copy_missing_source_raises(store):
    with pytest.raises(CopyError, match="Source snapshot not found"):
        copy_snapshot(store, "nonexistent", "snap2")


def test_copy_existing_destination_raises(store):
    _seed(store, "snap1")
    _seed(store, "snap2")
    with pytest.raises(CopyError, match="Destination snapshot already exists"):
        copy_snapshot(store, "snap1", "snap2")


def test_copy_result_summary(store):
    _seed(store, "snap1")
    result = copy_snapshot(store, "snap1", "snap2", profile="prod")
    summary = result.summary()
    assert "snap1" in summary
    assert "snap2" in summary
    assert "prod" in summary


def test_copy_across_profiles_independent(store):
    payload = b"bytes"
    _seed(store, "snap1", profile="dev", data=payload)
    result = copy_snapshot(store, "snap1", "snap1-backup", profile="dev")
    assert result.profile == "dev"
    assert store.load("snap1-backup", "dev") == payload
