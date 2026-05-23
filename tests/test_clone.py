"""Tests for envpack.clone."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envpack.clone import CloneError, CloneResult, _count_snapshots, clone_store


# ---------------------------------------------------------------------------
# _count_snapshots
# ---------------------------------------------------------------------------

def test_count_snapshots_empty_dir(tmp_path: Path) -> None:
    assert _count_snapshots(tmp_path) == 0


def test_count_snapshots_finds_enc_files(tmp_path: Path) -> None:
    (tmp_path / "snap1.enc").write_bytes(b"x")
    (tmp_path / "snap2.enc").write_bytes(b"x")
    (tmp_path / "readme.txt").write_text("ignore me")
    assert _count_snapshots(tmp_path) == 2


def test_count_snapshots_nested(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.enc").write_bytes(b"x")
    assert _count_snapshots(tmp_path) == 1


# ---------------------------------------------------------------------------
# CloneResult.summary
# ---------------------------------------------------------------------------

def test_clone_result_summary_contains_source_and_dest(tmp_path: Path) -> None:
    result = CloneResult(source="git@example.com:repo", destination=tmp_path, snapshot_count=3)
    summary = result.summary()
    assert "git@example.com:repo" in summary
    assert str(tmp_path) in summary
    assert "3 snapshot(s)" in summary


# ---------------------------------------------------------------------------
# clone_store – destination already exists
# ---------------------------------------------------------------------------

def test_clone_raises_when_destination_exists(tmp_path: Path) -> None:
    with pytest.raises(CloneError, match="already exists"):
        clone_store("git@example.com:repo", tmp_path)


# ---------------------------------------------------------------------------
# clone_store – git clone failure
# ---------------------------------------------------------------------------

def test_clone_raises_on_git_failure(tmp_path: Path) -> None:
    dest = tmp_path / "new_store"
    error = subprocess.CalledProcessError(128, "git", stderr="repository not found")
    with patch("envpack.clone.subprocess.run", side_effect=error):
        with pytest.raises(CloneError, match="repository not found"):
            clone_store("git@example.com:missing", dest)


# ---------------------------------------------------------------------------
# clone_store – success path
# ---------------------------------------------------------------------------

def test_clone_success_returns_result(tmp_path: Path) -> None:
    dest = tmp_path / "cloned"

    def _fake_run(cmd, **kwargs):
        # Simulate git clone by creating the destination with one snapshot
        dest.mkdir()
        (dest / "snap.enc").write_bytes(b"data")
        return MagicMock(returncode=0)

    with patch("envpack.clone.subprocess.run", side_effect=_fake_run):
        result = clone_store("git@example.com:repo", dest)

    assert isinstance(result, CloneResult)
    assert result.source == "git@example.com:repo"
    assert result.destination == dest
    assert result.snapshot_count == 1
