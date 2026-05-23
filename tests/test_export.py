"""Tests for envpack.export."""
import json
import pytest
from pathlib import Path

from envpack.export import ExportFormat, ExportError, export_snapshot, _parse_env


SAMPLE_ENV = """# comment
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
"""


# ---------------------------------------------------------------------------
# _parse_env
# ---------------------------------------------------------------------------

def test_parse_env_returns_key_value_pairs():
    result = _parse_env(SAMPLE_ENV)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


def test_parse_env_skips_comments_and_blanks():
    result = _parse_env(SAMPLE_ENV)
    for key in result:
        assert not key.startswith("#")


def test_parse_env_empty_string():
    assert _parse_env("") == {}


# ---------------------------------------------------------------------------
# export_snapshot — dotenv
# ---------------------------------------------------------------------------

def test_export_dotenv_format():
    output = export_snapshot(SAMPLE_ENV, ExportFormat.DOTENV)
    assert "DB_HOST=localhost" in output
    assert "DB_PORT=5432" in output
    assert output.endswith("\n")


def test_export_dotenv_excludes_comments():
    output = export_snapshot(SAMPLE_ENV, ExportFormat.DOTENV)
    assert "# comment" not in output


# ---------------------------------------------------------------------------
# export_snapshot — JSON
# ---------------------------------------------------------------------------

def test_export_json_is_valid_json():
    output = export_snapshot(SAMPLE_ENV, ExportFormat.JSON)
    data = json.loads(output)
    assert data["DB_HOST"] == "localhost"
    assert data["SECRET_KEY"] == "abc123"


# ---------------------------------------------------------------------------
# export_snapshot — shell
# ---------------------------------------------------------------------------

def test_export_shell_uses_export_prefix():
    output = export_snapshot(SAMPLE_ENV, ExportFormat.SHELL)
    assert "export DB_HOST=localhost" in output
    assert "export SECRET_KEY=abc123" in output


# ---------------------------------------------------------------------------
# file output
# ---------------------------------------------------------------------------

def test_export_writes_to_file(tmp_path):
    out_file = tmp_path / "subdir" / "out.env"
    export_snapshot(SAMPLE_ENV, ExportFormat.DOTENV, output_path=out_file)
    assert out_file.exists()
    assert "DB_HOST=localhost" in out_file.read_text()


def test_export_returns_content_even_when_writing_file(tmp_path):
    out_file = tmp_path / "out.json"
    result = export_snapshot(SAMPLE_ENV, ExportFormat.JSON, output_path=out_file)
    assert result == out_file.read_text()


# ---------------------------------------------------------------------------
# empty input
# ---------------------------------------------------------------------------

def test_export_empty_env_dotenv():
    assert export_snapshot("", ExportFormat.DOTENV) == ""


def test_export_empty_env_json():
    data = json.loads(export_snapshot("", ExportFormat.JSON))
    assert data == {}
