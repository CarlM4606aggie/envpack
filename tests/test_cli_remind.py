"""Tests for the remind CLI group."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envpack.cli_remind import remind_group
from envpack.config import Config
from envpack.remind import ReminderEntry, ReminderReport


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = tmp_path / "config.toml"
    cfg = Config(path=cfg_path)
    cfg.store_path = str(tmp_path / "store")
    cfg.save()
    monkeypatch.setenv("ENVPACK_CONFIG", str(cfg_path))
    monkeypatch.setenv("ENVPACK_PASSWORD", "secret")
    return cfg


def _fake_report(stale: bool = False) -> ReminderReport:
    from datetime import datetime, timezone
    now = datetime.now(tz=timezone.utc)
    entries = [
        ReminderEntry(
            name="prod",
            last_modified=now,
            age_days=50.0 if stale else 2.0,
            threshold_days=30,
        )
    ]
    return ReminderReport(entries=entries, threshold_days=30)


def test_check_no_stale_exits_zero(runner: CliRunner, isolated_config: Config):
    with patch("envpack.cli_remind.check_staleness", return_value=_fake_report(stale=False)), \
         patch("envpack.cli_remind._get_manager"):
        result = runner.invoke(remind_group, ["check", "--days", "30"])
    assert result.exit_code == 0
    assert "up to date" in result.output


def test_check_with_stale_exits_one(runner: CliRunner, isolated_config: Config):
    with patch("envpack.cli_remind.check_staleness", return_value=_fake_report(stale=True)), \
         patch("envpack.cli_remind._get_manager"):
        result = runner.invoke(remind_group, ["check", "--days", "30"])
    assert result.exit_code == 1
    assert "stale" in result.output


def test_list_prints_all_entries(runner: CliRunner, isolated_config: Config):
    with patch("envpack.cli_remind.check_staleness", return_value=_fake_report(stale=False)), \
         patch("envpack.cli_remind._get_manager"):
        result = runner.invoke(remind_group, ["list", "--days", "30"])
    assert result.exit_code == 0
    assert "prod" in result.output


def test_list_empty_store_message(runner: CliRunner, isolated_config: Config):
    empty_report = ReminderReport(entries=[], threshold_days=30)
    with patch("envpack.cli_remind.check_staleness", return_value=empty_report), \
         patch("envpack.cli_remind._get_manager"):
        result = runner.invoke(remind_group, ["list"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_stale_marker_shown(runner: CliRunner, isolated_config: Config):
    with patch("envpack.cli_remind.check_staleness", return_value=_fake_report(stale=True)), \
         patch("envpack.cli_remind._get_manager"):
        result = runner.invoke(remind_group, ["list", "--days", "30"])
    assert "STALE" in result.output
