"""Tests for envpack.cli_template."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envpack.cli_template import template_group
from envpack.config import Config
from envpack.crypto import encrypt


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated_config(tmp_path: Path):
    cfg = Config(store_path=str(tmp_path / "store"), password="testpass")
    return cfg


def _make_ctx_obj(cfg: Config):
    return {"config": cfg}


def _invoke(runner, cfg, args, input_text=None):
    return runner.invoke(
        template_group,
        args,
        obj=_make_ctx_obj(cfg),
        input=input_text,
        catch_exceptions=False,
    )


def test_render_to_stdout(runner, isolated_config, tmp_path):
    env_content = b"DB_HOST=localhost\nDB_PORT=5432\n"
    ciphertext = encrypt(env_content, "testpass")

    store_mock = MagicMock()
    store_mock.list_snapshots.return_value = ["snap1"]
    store_mock.load.return_value = ciphertext

    tmpl = tmp_path / "db.tmpl"
    tmpl.write_text("host={{ DB_HOST }} port={{ DB_PORT }}")

    with patch("envpack.cli_template.GitStore", return_value=store_mock):
        result = _invoke(runner, isolated_config, ["render", str(tmpl)])

    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "5432" in result.output


def test_render_to_file(runner, isolated_config, tmp_path):
    env_content = b"APP_NAME=envpack\n"
    ciphertext = encrypt(env_content, "testpass")
    out_file = tmp_path / "result.txt"

    store_mock = MagicMock()
    store_mock.list_snapshots.return_value = ["snap1"]
    store_mock.load.return_value = ciphertext

    tmpl = tmp_path / "app.tmpl"
    tmpl.write_text("name={{ APP_NAME }}")

    with patch("envpack.cli_template.GitStore", return_value=store_mock):
        result = _invoke(runner, isolated_config, ["render", str(tmpl), "-o", str(out_file)])

    assert result.exit_code == 0
    assert out_file.exists()
    assert out_file.read_text() == "name=envpack"


def test_render_strict_fails_on_missing(runner, isolated_config, tmp_path):
    env_content = b"A=1\n"
    ciphertext = encrypt(env_content, "testpass")

    store_mock = MagicMock()
    store_mock.list_snapshots.return_value = ["snap1"]
    store_mock.load.return_value = ciphertext

    tmpl = tmp_path / "strict.tmpl"
    tmpl.write_text("{{ MISSING_KEY }}")

    with patch("envpack.cli_template.GitStore", return_value=store_mock):
        result = runner.invoke(
            template_group,
            ["render", str(tmpl), "--strict"],
            obj=_make_ctx_obj(isolated_config),
        )

    assert result.exit_code != 0
    assert "MISSING_KEY" in result.output


def test_render_no_snapshots_fails(runner, isolated_config, tmp_path):
    store_mock = MagicMock()
    store_mock.list_snapshots.return_value = []

    tmpl = tmp_path / "t.tmpl"
    tmpl.write_text("{{ X }}")

    with patch("envpack.cli_template.GitStore", return_value=store_mock):
        result = runner.invoke(
            template_group,
            ["render", str(tmpl)],
            obj=_make_ctx_obj(isolated_config),
        )

    assert result.exit_code != 0
    assert "No snapshots" in result.output
