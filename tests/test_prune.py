"""Tests for envpack.prune."""

from __future__ import annotations

import pytest

from envpack.prune import PruneError, PruneResult, prune_snapshots
from envpack.store import GitStore


@pytest.fixture()
def store(tmp_path):
    s = GitStore(tmp_path / "store")
    s.init()
    return s


def _seed(store: GitStore, profile: str, names: list[str], content: bytes = b"data") -> None:
    for name in names:
        store.save(profile, name, content)


# ---------------------------------------------------------------------------
# PruneResult helpers
# ---------------------------------------------------------------------------

def test_prune_result_summary_nothing_removed():
    result = PruneResult(kept=["a", "b"], removed=[])
    assert "Nothing to prune" in result.summary()
    assert "2" in result.summary()


def test_prune_result_summary_some_removed():
    result = PruneResult(kept=["c"], removed=["a", "b"])
    assert "Pruned 2" in result.summary()
    assert "1 retained" in result.summary()


# ---------------------------------------------------------------------------
# prune_snapshots
# ---------------------------------------------------------------------------

def test_prune_keep_more_than_available_keeps_all(store):
    _seed(store, "dev", ["2024-01-01.env", "2024-01-02.env"])
    result = prune_snapshots(store, "dev", keep=10)
    assert len(result.removed) == 0
    assert len(result.kept) == 2


def test_prune_removes_oldest_snapshots(store):
    names = [
        "2024-01-01T00.env",
        "2024-01-02T00.env",
        "2024-01-03T00.env",
        "2024-01-04T00.env",
    ]
    _seed(store, "prod", names)
    result = prune_snapshots(store, "prod", keep=2)
    assert result.removed == ["2024-01-01T00.env", "2024-01-02T00.env"]
    assert result.kept == ["2024-01-03T00.env", "2024-01-04T00.env"]


def test_prune_keep_one_retains_most_recent(store):
    names = ["2024-03-01.env", "2024-03-02.env", "2024-03-03.env"]
    _seed(store, "staging", names)
    result = prune_snapshots(store, "staging", keep=1)
    assert result.kept == ["2024-03-03.env"]
    assert len(result.removed) == 2


def test_prune_empty_profile_returns_empty_result(store):
    result = prune_snapshots(store, "empty-profile", keep=3)
    assert result.kept == []
    assert result.removed == []


def test_prune_keep_zero_raises(store):
    with pytest.raises(PruneError, match="at least 1"):
        prune_snapshots(store, "dev", keep=0)


def test_prune_keep_negative_raises(store):
    with pytest.raises(PruneError, match="at least 1"):
        prune_snapshots(store, "dev", keep=-5)


def test_prune_removed_snapshots_no_longer_listed(store):
    names = ["snap-1.env", "snap-2.env", "snap-3.env"]
    _seed(store, "ci", names)
    prune_snapshots(store, "ci", keep=1)
    remaining = store.list_snapshots("ci")
    assert remaining == ["snap-3.env"]
