"""Tests for envpack.search."""
from __future__ import annotations

import pytest
from pathlib import Path

from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.search import search_snapshots, SearchMatch, SearchResult, _parse_env


PASSWORD = "hunter2"


@pytest.fixture()
def store(tmp_path: Path) -> GitStore:
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _save(store: GitStore, name: str, content: str) -> None:
    store.save(name, encrypt(content.encode(), PASSWORD))


# --- _parse_env ---

def test_parse_env_basic():
    result = _parse_env("FOO=bar\nBAZ=qux")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_skips_comments():
    result = _parse_env("# comment\nFOO=bar")
    assert "# comment" not in result
    assert result["FOO"] == "bar"


def test_parse_env_skips_blank_lines():
    result = _parse_env("\n\nFOO=bar\n")
    assert result == {"FOO": "bar"}


# --- search_snapshots ---

def test_search_by_key_glob(store: GitStore):
    _save(store, "snap1", "DB_HOST=localhost\nDB_PORT=5432")
    result = search_snapshots(store, PASSWORD, key_pattern="DB_*")
    assert result.has_matches
    keys = {m.key for m in result.matches}
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys


def test_search_by_value_glob(store: GitStore):
    _save(store, "snap1", "API_URL=https://example.com\nOTHER=nope")
    result = search_snapshots(store, PASSWORD, value_pattern="https://*")
    assert result.has_matches
    assert result.matches[0].key == "API_URL"


def test_search_no_match_returns_empty(store: GitStore):
    _save(store, "snap1", "FOO=bar")
    result = search_snapshots(store, PASSWORD, key_pattern="MISSING_*")
    assert not result.has_matches


def test_search_across_multiple_snapshots(store: GitStore):
    _save(store, "snap1", "SECRET=abc")
    _save(store, "snap2", "SECRET=xyz")
    result = search_snapshots(store, PASSWORD, key_pattern="SECRET")
    snapshots = {m.snapshot for m in result.matches}
    assert "snap1" in snapshots
    assert "snap2" in snapshots


def test_search_with_snapshot_glob_filters(store: GitStore):
    _save(store, "prod-snap", "KEY=val")
    _save(store, "dev-snap", "KEY=val")
    result = search_snapshots(store, PASSWORD, key_pattern="KEY", snapshot_glob="prod-*")
    assert all(m.snapshot.startswith("prod") for m in result.matches)


def test_search_bad_password_skips_snapshot(store: GitStore):
    _save(store, "snap1", "FOO=bar")
    result = search_snapshots(store, "wrongpass", key_pattern="FOO")
    assert not result.has_matches


def test_search_result_summary_no_matches():
    r = SearchResult()
    assert r.summary() == "No matches found."


def test_search_result_summary_with_matches():
    r = SearchResult(matches=[SearchMatch("snap1", "FOO", "bar")])
    assert "snap1" in r.summary()
    assert "FOO" in r.summary()
