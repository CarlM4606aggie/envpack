"""Tests for envpack.template."""

from pathlib import Path

import pytest

from envpack.template import (
    RenderResult,
    TemplateError,
    _parse_env,
    render_template,
    render_template_file,
)

ENV_TEXT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


# --- _parse_env ---

def test_parse_env_basic():
    result = _parse_env("A=1\nB=2\n")
    assert result == {"A": "1", "B": "2"}


def test_parse_env_skips_comments():
    result = _parse_env("# comment\nA=1\n")
    assert "# comment" not in result
    assert result["A"] == "1"


def test_parse_env_skips_blanks():
    result = _parse_env("\n\nA=1\n")
    assert result == {"A": "1"}


def test_parse_env_empty_value():
    result = _parse_env("EMPTY=\n")
    assert result["EMPTY"] == ""


# --- render_template ---

def test_render_fills_placeholder():
    result = render_template("host={{ DB_HOST }}", ENV_TEXT)
    assert result.rendered == "host=localhost"
    assert "DB_HOST" in result.filled


def test_render_leaves_unknown_placeholder():
    result = render_template("x={{ UNKNOWN }}", ENV_TEXT)
    assert "{{ UNKNOWN }}" in result.rendered
    assert "UNKNOWN" in result.missing


def test_render_multiple_placeholders():
    tmpl = "{{DB_HOST}}:{{DB_PORT}}"
    result = render_template(tmpl, ENV_TEXT)
    assert result.rendered == "localhost:5432"
    assert len(result.filled) == 2


def test_render_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="UNKNOWN"):
        render_template("{{ UNKNOWN }}", ENV_TEXT, strict=True)


def test_render_strict_succeeds_when_all_present():
    result = render_template("{{ DB_HOST }}", ENV_TEXT, strict=True)
    assert result.rendered == "localhost"


def test_render_result_summary_no_missing():
    result = RenderResult(rendered="x", filled=["A", "B"], missing=[])
    assert "filled=2" in result.summary()
    assert "missing" not in result.summary()


def test_render_result_summary_with_missing():
    result = RenderResult(rendered="x", filled=["A"], missing=["B"])
    assert "missing=1" in result.summary()
    assert "B" in result.summary()


# --- render_template_file ---

def test_render_template_file_fills_values(tmp_path: Path):
    tmpl = tmp_path / "template.txt"
    tmpl.write_text("host={{ DB_HOST }}")
    result = render_template_file(tmpl, ENV_TEXT)
    assert result.rendered == "host=localhost"


def test_render_template_file_writes_output(tmp_path: Path):
    tmpl = tmp_path / "template.txt"
    tmpl.write_text("port={{ DB_PORT }}")
    out = tmp_path / "out" / "result.txt"
    render_template_file(tmpl, ENV_TEXT, output_path=out)
    assert out.exists()
    assert out.read_text() == "port=5432"


def test_render_template_file_missing_template_raises(tmp_path: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_template_file(tmp_path / "ghost.txt", ENV_TEXT)
