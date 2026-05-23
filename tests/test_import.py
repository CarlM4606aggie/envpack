"""Tests for envpack.import_ module."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envpack.import_ import (
    ImportError,
    ImportResult,
    _count_keys,
    _validate_snapshot_name,
    import_env_file,
)


# ---------------------------------------------------------------------------
# _count_keys
# ---------------------------------------------------------------------------

def test_count_keys_basic():
    content = "DB_HOST=localhost\nDB_PORT=5432\n"
    assert _count_keys(content) == 2


def test_count_keys_skips_comments():
    content = "# comment\nKEY=value\n"
    assert _count_keys(content) == 1


def test_count_keys_skips_blank_lines():
    content = "\n\nKEY=value\n\n"
    assert _count_keys(content) == 1


def test_count_keys_skips_lines_without_equals():
    content = "NOEQUALS\nKEY=value\n"
    assert _count_keys(content) == 1


def test_count_keys_empty_string():
    assert _count_keys("") == 0


# ---------------------------------------------------------------------------
# _validate_snapshot_name
# ---------------------------------------------------------------------------

def test_validate_snapshot_name_valid():
    _validate_snapshot_name("my-snapshot")
    _validate_snapshot_name("snap_v1.0")
    _validate_snapshot_name("ABC123")


def test_validate_snapshot_name_empty_raises():
    with pytest.raises(ImportError, match="must not be empty"):
        _validate_snapshot_name("")


def test_validate_snapshot_name_spaces_raises():
    with pytest.raises(ImportError, match="Invalid snapshot name"):
        _validate_snapshot_name("bad name")


def test_validate_snapshot_name_slash_raises():
    with pytest.raises(ImportError, match="Invalid snapshot name"):
        _validate_snapshot_name("bad/name")


# ---------------------------------------------------------------------------
# import_env_file
# ---------------------------------------------------------------------------

@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nSECRET=abc123\n")
    return f


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.store = MagicMock()
    return manager


def test_import_returns_result(env_file, mock_manager):
    result = import_env_file(env_file, "prod", mock_manager, "pass")
    assert isinstance(result, ImportResult)
    assert result.snapshot_name == "prod"
    assert result.keys_imported == 2
    assert str(env_file) in result.source_path


def test_import_calls_store_save(env_file, mock_manager):
    import_env_file(env_file, "prod", mock_manager, "pass")
    mock_manager.store.save.assert_called_once()
    call_args = mock_manager.store.save.call_args
    assert call_args[0][0] == "prod"


def test_import_missing_file_raises(tmp_path, mock_manager):
    missing = tmp_path / "missing.env"
    with pytest.raises(ImportError, match="does not exist"):
        import_env_file(missing, "snap", mock_manager, "pass")


def test_import_directory_raises(tmp_path, mock_manager):
    with pytest.raises(ImportError, match="not a file"):
        import_env_file(tmp_path, "snap", mock_manager, "pass")


def test_import_empty_env_raises(tmp_path, mock_manager):
    empty = tmp_path / ".env"
    empty.write_text("# only a comment\n")
    with pytest.raises(ImportError, match="No valid KEY=VALUE"):
        import_env_file(empty, "snap", mock_manager, "pass")


def test_import_result_summary():
    result = ImportResult("prod", 5, "/path/.env")
    summary = result.summary()
    assert "5" in summary
    assert "prod" in summary
    assert "/path/.env" in summary
