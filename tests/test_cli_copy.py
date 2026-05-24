"""Tests for the copy CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envpack.cli import cli
from envpack.config import Config
from envpack.store import GitStore


@pytest.fixture()
def isolated_config(tmp_path):
    store_dir = tmp_path / "store"
    cfg = Config(path=tmp_path / "config.json")
    cfg.store_path = str(store_dir)
    cfg.save()
    s = GitStore(store_dir)
    s.init()
    return cfg


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


def _seed(cfg: Config, name: str, data: bytes = b"payload") -> None:
    s = GitStore(cfg.store_path)
    s.save(name, cfg.profile, data)


def test_copy_run_success(isolated_config, runner, tmp_path):
    _seed(isolated_config, "snap1")
    result = runner.invoke(
        cli,
        [
            "--config", str(isolated_config.path),
            "copy", "run", "snap1", "snap2",
            "--password", "secret",
        ],
    )
    assert result.exit_code == 0
    assert "snap1" in result.output
    assert "snap2" in result.output


def test_copy_run_missing_source_fails(isolated_config, runner):
    result = runner.invoke(
        cli,
        [
            "--config", str(isolated_config.path),
            "copy", "run", "missing", "dest",
            "--password", "secret",
        ],
    )
    assert result.exit_code != 0


def test_copy_run_duplicate_destination_fails(isolated_config, runner):
    _seed(isolated_config, "snap1")
    _seed(isolated_config, "snap2")
    result = runner.invoke(
        cli,
        [
            "--config", str(isolated_config.path),
            "copy", "run", "snap1", "snap2",
            "--password", "secret",
        ],
    )
    assert result.exit_code != 0
    assert "already exists" in result.stderr
