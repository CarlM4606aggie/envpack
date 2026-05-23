"""Tests for envpack.cli_verify."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envpack.cli import cli
from envpack.store import GitStore
from envpack.crypto import encrypt
from envpack.config import Config


PASSWORD = "testpass"
PROFILE = "default"


@pytest.fixture()
def isolated_config(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    config_path = tmp_path / "config.json"
    cfg = Config(store_path=store_dir, profile=PROFILE)
    cfg.save(config_path)
    monkeypatch.setenv("ENVPACK_CONFIG", str(config_path))
    store = GitStore(store_dir)
    store.init()
    return {"store": store, "config_path": config_path}


@pytest.fixture()
def runner():
    return CliRunner()


def _seed(store: GitStore, name: str, plaintext: bytes) -> None:
    ciphertext = encrypt(plaintext, PASSWORD)
    store.save(PROFILE, name, ciphertext)


def test_verify_empty_store_exits_zero(isolated_config, runner):
    result = runner.invoke(cli, ["verify", "run", "--password", PASSWORD])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_verify_valid_snapshots_exits_zero(isolated_config, runner):
    _seed(isolated_config["store"], "snap1", b"KEY=val")
    result = runner.invoke(cli, ["verify", "run", "--password", PASSWORD])
    assert result.exit_code == 0
    assert "verified successfully" in result.output


def test_verify_wrong_password_exits_nonzero(isolated_config, runner):
    _seed(isolated_config["store"], "snap1", b"KEY=val")
    result = runner.invoke(cli, ["verify", "run", "--password", "wrongpass"])
    assert result.exit_code != 0
    assert "FAIL" in result.output


def test_verify_shows_checkmark_for_good_snapshot(isolated_config, runner):
    _seed(isolated_config["store"], "snap1", b"A=1")
    result = runner.invoke(cli, ["verify", "run", "--password", PASSWORD])
    assert "snap1" in result.output
    assert "OK" in result.output
