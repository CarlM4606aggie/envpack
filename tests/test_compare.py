"""Tests for envpack.compare."""
from __future__ import annotations

import pytest

from envpack.compare import (
    compare_snapshots,
    CompareError,
    CompareResult,
    KeyDiff,
    _parse_env,
)
from envpack.crypto import encrypt
from envpack.store import GitStore


PASSWORD = "test-secret"


@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _save(store: GitStore, name: str, content: str) -> None:
    store.save(name, encrypt(content.encode(), PASSWORD))


# --- _parse_env ---

def test_parse_env_basic():
    text = "KEY=value\nFOO=bar"
    assert _parse_env(text) == {"KEY": "value", "FOO": "bar"}


def test_parse_env_skips_comments():
    text = "# comment\nKEY=value"
    assert _parse_env(text) == {"KEY": "value"}


def test_parse_env_skips_blank_lines():
    text = "\nKEY=value\n\n"
    assert _parse_env(text) == {"KEY": "value"}


def test_parse_env_skips_lines_without_equals():
    assert _parse_env("NOEQUALS") == {}


# --- compare_snapshots ---

def test_identical_snapshots_have_no_diffs(store):
    content = "KEY=val\nFOO=bar\n"
    _save(store, "snap-a", content)
    _save(store, "snap-b", content)
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    assert not result.has_differences
    assert result.diffs == []


def test_changed_key_detected(store):
    _save(store, "snap-a", "KEY=old\n")
    _save(store, "snap-b", "KEY=new\n")
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    assert result.has_differences
    assert len(result.diffs) == 1
    assert result.diffs[0].key == "KEY"
    assert result.diffs[0].status == "changed"


def test_added_key_detected(store):
    _save(store, "snap-a", "KEY=val\n")
    _save(store, "snap-b", "KEY=val\nNEW=extra\n")
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    assert any(d.key == "NEW" and d.status == "added" for d in result.diffs)


def test_removed_key_detected(store):
    _save(store, "snap-a", "KEY=val\nOLD=gone\n")
    _save(store, "snap-b", "KEY=val\n")
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    assert any(d.key == "OLD" and d.status == "removed" for d in result.diffs)


def test_missing_snapshot_raises(store):
    _save(store, "snap-a", "KEY=val\n")
    with pytest.raises(CompareError, match="Snapshot not found"):
        compare_snapshots(store, "snap-a", "nonexistent", PASSWORD)


def test_summary_identical(store):
    content = "KEY=val\n"
    _save(store, "snap-a", content)
    _save(store, "snap-b", content)
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    assert "identical" in result.summary()


def test_summary_with_diffs(store):
    _save(store, "snap-a", "KEY=old\n")
    _save(store, "snap-b", "KEY=new\nEXTRA=1\n")
    result = compare_snapshots(store, "snap-a", "snap-b", PASSWORD)
    summary = result.summary()
    assert "changed" in summary
    assert "added" in summary


def test_key_diff_str_added():
    d = KeyDiff(key="FOO", left_value=None, right_value="bar")
    assert str(d).startswith("  +")
    assert "FOO" in str(d)


def test_key_diff_str_removed():
    d = KeyDiff(key="FOO", left_value="bar", right_value=None)
    assert str(d).startswith("  -")


def test_key_diff_str_changed():
    d = KeyDiff(key="FOO", left_value="old", right_value="new")
    assert str(d).startswith("  ~")
