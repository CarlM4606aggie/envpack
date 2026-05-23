"""Tests for the compress CLI commands."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from envpack.cli_compress import compress_group
from envpack.config import Config
from envpack.crypto import encrypt
from envpack.store import GitStore


@pytest.fixture()
def isolated_config(tmp_path: Path):
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    store = GitStore(store_dir)
    store.init()
    cfg = Config(store_path=store_dir)
    return cfg, store


@pytest.fixture()
def runner():
    return CliRunner()


def test_estimate_shows_stats(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\nOTHER=123\n" * 20)
    result = runner.invoke(compress_group, ["estimate", str(env_file)])
    assert result.exit_code == 0
    assert "Stats" in result.output
    assert "->" in result.output


def test_estimate_missing_file_fails(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(compress_group, ["estimate", str(tmp_path / "missing.env")])
    assert result.exit_code != 0


def test_compress_stats_valid_snapshot(runner: CliRunner, isolated_config, tmp_path: Path):
    cfg, store = isolated_config
    password = "secret"
    plaintext = b"DB=postgres\nSECRET=abc\n"
    ciphertext = encrypt(plaintext, password)
    store.save("mysnap", ciphertext)

    result = runner.invoke(
        compress_group,
        ["stats", "mysnap", "--password", password],
        obj={"config": cfg},
    )
    assert result.exit_code == 0
    assert "mysnap" in result.output
    assert "->" in result.output


def test_compress_stats_wrong_password(runner: CliRunner, isolated_config):
    cfg, store = isolated_config
    ciphertext = encrypt(b"KEY=val\n", "correct")
    store.save("snap2", ciphertext)

    result = runner.invoke(
        compress_group,
        ["stats", "snap2", "--password", "wrong"],
        obj={"config": cfg},
    )
    assert result.exit_code != 0
    assert "Decryption failed" in result.output


def test_compress_stats_missing_snapshot(runner: CliRunner, isolated_config):
    cfg, _ = isolated_config
    result = runner.invoke(
        compress_group,
        ["stats", "nonexistent", "--password", "pass"],
        obj={"config": cfg},
    )
    assert result.exit_code != 0
