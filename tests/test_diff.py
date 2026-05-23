"""Tests for envpack.diff module."""

import pytest

from envpack.diff import EnvDiff, _parse_env, diff_env_texts


# ---------------------------------------------------------------------------
# _parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    result = _parse_env(text)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_skips_comments():
    text = "# comment\nFOO=1\n"
    result = _parse_env(text)
    assert "FOO" in result
    assert len(result) == 1


def test_parse_env_skips_blank_lines():
    text = "\n  \nFOO=1\n"
    assert _parse_env(text) == {"FOO": "1"}


def test_parse_env_skips_lines_without_equals():
    text = "NOEQUALS\nFOO=bar\n"
    assert _parse_env(text) == {"FOO": "bar"}


def test_parse_env_empty_value():
    text = "EMPTY=\n"
    assert _parse_env(text) == {"EMPTY": ""}


# ---------------------------------------------------------------------------
# diff_env_texts
# ---------------------------------------------------------------------------

OLD = "FOO=1\nBAR=old\nKEEP=same\n"
NEW = "BAR=new\nKEEP=same\nBQUX=added\n"


def test_diff_added_keys():
    d = diff_env_texts(OLD, NEW)
    assert "BQUX" in d.added
    assert d.added["BQUX"] == "added"


def test_diff_removed_keys():
    d = diff_env_texts(OLD, NEW)
    assert "FOO" in d.removed


def test_diff_changed_keys():
    d = diff_env_texts(OLD, NEW)
    assert "BAR" in d.changed
    assert d.changed["BAR"] == ("old", "new")


def test_diff_unchanged_keys():
    d = diff_env_texts(OLD, NEW)
    assert "KEEP" in d.unchanged


def test_diff_has_changes_true():
    assert diff_env_texts(OLD, NEW).has_changes


def test_diff_has_changes_false():
    assert not diff_env_texts(OLD, OLD).has_changes


def test_diff_none_old_treats_as_empty():
    d = diff_env_texts(None, "FOO=1\n")
    assert "FOO" in d.added
    assert not d.removed


def test_diff_none_new_treats_as_empty():
    d = diff_env_texts("FOO=1\n", None)
    assert "FOO" in d.removed
    assert not d.added


def test_summary_no_changes():
    d = diff_env_texts(OLD, OLD)
    assert d.summary() == "(no changes)"


def test_summary_contains_added_prefix():
    d = diff_env_texts("", "NEW_KEY=val\n")
    assert d.summary().startswith("+")
