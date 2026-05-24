"""Tests for envpack.cli_pin."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envpack.cli_pin import pin_group
from envpack.config import Config


@pytest.fixture()
def isolated_config(tmp_path: Path):
    cfg = Config(store_path=str(tmp_path / "store"), profile="default")
    (tmp_path / "store").mkdir(parents=True, exist_ok=True)
    return cfg


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, cfg, *args):
    return runner.invoke(pin_group, list(args), obj={"config": cfg})


# ---------------------------------------------------------------------------

def test_list_empty(runner, isolated_config):
    result = _invoke(runner, isolated_config, "list")
    assert result.exit_code == 0
    assert "No pinned" in result.output


def test_set_pin(runner, isolated_config):
    result = _invoke(runner, isolated_config, "set", "snap1")
    assert result.exit_code == 0
    assert "Pinned" in result.output


def test_list_after_set(runner, isolated_config):
    _invoke(runner, isolated_config, "set", "snap1")
    result = _invoke(runner, isolated_config, "list")
    assert "snap1" in result.output


def test_unset_pin(runner, isolated_config):
    _invoke(runner, isolated_config, "set", "snap1")
    result = _invoke(runner, isolated_config, "unset", "snap1")
    assert result.exit_code == 0
    assert "Unpinned" in result.output


def test_check_pinned_exits_zero(runner, isolated_config):
    _invoke(runner, isolated_config, "set", "snap1")
    result = _invoke(runner, isolated_config, "check", "snap1")
    assert result.exit_code == 0
    assert "is pinned" in result.output


def test_check_not_pinned_exits_one(runner, isolated_config):
    result = _invoke(runner, isolated_config, "check", "missing")
    assert result.exit_code == 1
    assert "not pinned" in result.output
