"""Tests for envpack.lint."""
from __future__ import annotations

import pytest
from pathlib import Path

from envpack.lint import LintError, LintIssue, LintResult, lint_env_text, lint_file


# ---------------------------------------------------------------------------
# lint_env_text
# ---------------------------------------------------------------------------

def test_clean_env_returns_ok():
    text = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = lint_env_text(text)
    assert result.ok
    assert result.issues == []


def test_missing_equals_raises_e001():
    result = lint_env_text("BADLINE\n")
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_invalid_key_name_raises_e002():
    result = lint_env_text("123BAD=value\n")
    codes = [i.code for i in result.issues]
    assert "E002" in codes


def test_duplicate_key_raises_w001():
    text = "KEY=one\nKEY=two\n"
    result = lint_env_text(text)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_unquoted_value_with_spaces_raises_w002():
    result = lint_env_text("GREETING=hello world\n")
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_quoted_value_with_spaces_is_ok():
    result = lint_env_text('GREETING="hello world"\n')
    assert result.ok


def test_comments_and_blank_lines_ignored():
    text = "# a comment\n\nVALID=yes\n"
    result = lint_env_text(text)
    assert result.ok


def test_empty_value_is_ok():
    result = lint_env_text("EMPTY=\n")
    assert result.ok


def test_summary_no_issues():
    result = LintResult(path="test.env")
    assert "no issues" in result.summary()


def test_summary_with_issues():
    result = LintResult(path="test.env", issues=[LintIssue(1, "E001", "bad")])
    summary = result.summary()
    assert "1 issue" in summary
    assert "E001" in summary


def test_lint_issue_str():
    issue = LintIssue(3, "W001", "Duplicate key 'X'")
    assert "Line 3" in str(issue)
    assert "W001" in str(issue)


# ---------------------------------------------------------------------------
# lint_file
# ---------------------------------------------------------------------------

def test_lint_file_reads_from_disk(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\nPORT=8080\n")
    result = lint_file(env_file)
    assert result.ok


def test_lint_file_missing_raises(tmp_path: Path):
    with pytest.raises(LintError, match="not found"):
        lint_file(tmp_path / "nonexistent.env")


def test_lint_file_path_in_result(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=val\n")
    result = lint_file(env_file)
    assert str(env_file) in result.path
