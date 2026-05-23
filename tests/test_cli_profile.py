"""Integration tests for the profile CLI sub-commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envpack.cli_profile import profile_group
from envpack.config import Config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect config and store to a temporary directory."""
    store_path = tmp_path / "store"
    store_path.mkdir()
    cfg = Config(store_path=store_path, profile="default")
    cfg.save()
    monkeypatch.setenv("ENVPACK_CONFIG", str(cfg._path if hasattr(cfg, "_path") else tmp_path / "config.json"))
    # Patch Config.load to return our temp config
    monkeypatch.setattr(
        "envpack.cli_profile.Config.load",
        lambda: Config(store_path=store_path, profile="default"),
    )
    return store_path


@pytest.fixture()
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create_profile(runner):
    result = runner.invoke(profile_group, ["create", "dev", "-d", "Dev env", "-t", "local"])
    assert result.exit_code == 0
    assert "created" in result.output


def test_create_duplicate_profile_fails(runner):
    runner.invoke(profile_group, ["create", "dev"])
    result = runner.invoke(profile_group, ["create", "dev"])
    assert result.exit_code != 0
    assert "already exists" in result.output


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_empty(runner):
    result = runner.invoke(profile_group, ["list"])
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_list_shows_created_profiles(runner):
    runner.invoke(profile_group, ["create", "prod"])
    runner.invoke(profile_group, ["create", "staging"])
    result = runner.invoke(profile_group, ["list"])
    assert "prod" in result.output
    assert "staging" in result.output


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def test_show_profile(runner):
    runner.invoke(profile_group, ["create", "ci", "-d", "CI pipeline", "-t", "cloud"])
    result = runner.invoke(profile_group, ["show", "ci"])
    assert result.exit_code == 0
    assert "CI pipeline" in result.output
    assert "cloud" in result.output


def test_show_missing_profile_fails(runner):
    result = runner.invoke(profile_group, ["show", "ghost"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_profile(runner):
    runner.invoke(profile_group, ["create", "tmp"])
    result = runner.invoke(profile_group, ["delete", "tmp"], input="y\n")
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_profile_fails(runner):
    result = runner.invoke(profile_group, ["delete", "ghost"], input="y\n")
    assert result.exit_code != 0
