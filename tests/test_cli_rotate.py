"""CLI tests for envpack rotate."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envpack.cli_rotate import rotate_group
from envpack.config import Config
from envpack.crypto import encrypt
from envpack.store import GitStore


OLD = "old-pass"
NEW = "new-pass"


@pytest.fixture()
def isolated_config(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    store_dir = tmp_path / "store"
    monkeypatch.setenv("ENVPACK_CONFIG", str(cfg_path))
    cfg = Config(store_path=str(store_dir), profile="default")
    cfg.save(cfg_path)
    s = GitStore(store_dir)
    s.init()
    ct = encrypt(b"KEY=val", OLD)
    s.save("default", "snap1", ct, message="seed")
    return cfg_path, store_dir


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


def test_rotate_run_success(isolated_config, runner, monkeypatch):
    cfg_path, store_dir = isolated_config
    monkeypatch.setattr(
        "envpack.cli_rotate.Config.load",
        lambda: Config(store_path=str(store_dir), profile="default"),
    )
    result = runner.invoke(
        rotate_group,
        ["run", "--old-password", OLD, "--new-password", NEW],
    )
    assert result.exit_code == 0, result.output
    assert "Rotated: 1" in result.output


def test_rotate_run_wrong_password_fails(isolated_config, runner, monkeypatch):
    cfg_path, store_dir = isolated_config
    monkeypatch.setattr(
        "envpack.cli_rotate.Config.load",
        lambda: Config(store_path=str(store_dir), profile="default"),
    )
    result = runner.invoke(
        rotate_group,
        ["run", "--old-password", "wrong", "--new-password", NEW],
    )
    assert result.exit_code != 0
    assert "Failed: 1" in result.output


def test_rotate_run_empty_store_exits_zero(isolated_config, runner, monkeypatch, tmp_path):
    empty_store = tmp_path / "empty"
    s = GitStore(empty_store)
    s.init()
    monkeypatch.setattr(
        "envpack.cli_rotate.Config.load",
        lambda: Config(store_path=str(empty_store), profile="default"),
    )
    result = runner.invoke(
        rotate_group,
        ["run", "--old-password", OLD, "--new-password", NEW],
    )
    assert result.exit_code == 0
    assert "Rotated: 0" in result.output
