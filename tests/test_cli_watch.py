"""Tests for envpack.cli_watch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envpack.cli_watch import watch_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = tmp_path / "envpack.toml"
    monkeypatch.setenv("ENVPACK_CONFIG", str(cfg_path))
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    return tmp_path


def test_watch_start_calls_watch_file(isolated_config: Path, runner: CliRunner) -> None:
    env_file = isolated_config / ".env"
    env_file.write_text("KEY=val")

    mock_manager = MagicMock()

    with (
        patch("envpack.cli_watch._get_manager", return_value=mock_manager),
        patch("envpack.cli_watch.Config.load", return_value=MagicMock()),
        patch("envpack.cli_watch.watch_file") as mock_watch,
    ):
        result = runner.invoke(
            watch_group,
            ["start", str(env_file), "--password", "secret", "--interval", "1"],
        )

    assert result.exit_code == 0
    mock_watch.assert_called_once()


def test_watch_start_missing_file_fails(isolated_config: Path, runner: CliRunner) -> None:
    missing = isolated_config / "no_such.env"
    result = runner.invoke(
        watch_group,
        ["start", str(missing), "--password", "secret"],
    )
    assert result.exit_code != 0


def test_watch_start_keyboard_interrupt_exits_cleanly(
    isolated_config: Path, runner: CliRunner
) -> None:
    env_file = isolated_config / ".env"
    env_file.write_text("A=1")

    with (
        patch("envpack.cli_watch._get_manager", return_value=MagicMock()),
        patch("envpack.cli_watch.Config.load", return_value=MagicMock()),
        patch("envpack.cli_watch.watch_file", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            watch_group,
            ["start", str(env_file), "--password", "pw"],
        )

    assert result.exit_code == 0
    assert "stopped" in result.output.lower()
