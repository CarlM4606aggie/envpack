"""CLI tests for the rename command group."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envpack.cli import cli
from envpack.config import Config
from envpack.crypto import encrypt
from envpack.store import GitStore


PASSWORD = "s3cr3t"
PLAINTEXT = b"KEY=value\n"


@pytest.fixture()
def isolated_config(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    store_path = tmp_path / "store"
    cfg = Config(path=cfg_path)
    cfg.store_path = str(store_path)
    cfg.save()
    monkeypatch.setenv("ENVPACK_CONFIG", str(cfg_path))
    s = GitStore(str(store_path))
    s.init()
    return cfg, s


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


def _seed(store: GitStore, name: str) -> None:
    store.save(name, encrypt(PLAINTEXT, PASSWORD))


def test_rename_run_success(isolated_config, runner):
    cfg, store = isolated_config
    _seed(store, "snap1")
    result = runner.invoke(
        cli,
        ["rename", "run", "snap1", "snap2", "--password", PASSWORD],
    )
    assert result.exit_code == 0, result.output
    assert "snap1" in result.output
    assert "snap2" in result.output


def test_rename_run_missing_snapshot_fails(isolated_config, runner):
    _cfg, _store = isolated_config
    result = runner.invoke(
        cli,
        ["rename", "run", "ghost", "new", "--password", PASSWORD],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "error" in result.output.lower()


def test_rename_run_duplicate_target_fails(isolated_config, runner):
    cfg, store = isolated_config
    _seed(store, "a")
    _seed(store, "b")
    result = runner.invoke(
        cli,
        ["rename", "run", "a", "b", "--password", PASSWORD],
    )
    assert result.exit_code != 0
