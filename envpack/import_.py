"""Import snapshots from external .env files or other formats into the envpack store."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


@dataclass
class ImportResult:
    snapshot_name: str
    keys_imported: int
    source_path: str

    def summary(self) -> str:
        return (
            f"Imported {self.keys_imported} key(s) from '{self.source_path}' "
            f"as snapshot '{self.snapshot_name}'."
        )


def _read_env_file(path: Path) -> str:
    """Read and return the raw content of an env file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ImportError(f"Cannot read file '{path}': {exc}") from exc


def _count_keys(content: str) -> int:
    """Count the number of valid KEY=VALUE pairs in env content."""
    count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            count += 1
    return count


def _validate_snapshot_name(name: str) -> None:
    """Validate that a snapshot name is safe to use as a filename."""
    if not name:
        raise ImportError("Snapshot name must not be empty.")
    if not re.match(r"^[\w\-\.]+$", name):
        raise ImportError(
            f"Invalid snapshot name '{name}'. Use only letters, digits, hyphens, "
            "underscores, and dots."
        )


def import_env_file(
    source: Path,
    snapshot_name: str,
    manager,  # SnapshotManager
    password: str,
    profile: Optional[str] = None,
) -> ImportResult:
    """Import a .env file into the store as a named snapshot.

    Args:
        source: Path to the source .env file.
        snapshot_name: Name to assign to the imported snapshot.
        manager: A SnapshotManager instance used to save the snapshot.
        password: Encryption password.
        profile: Optional profile to associate with the snapshot.

    Returns:
        ImportResult with details about the import.
    """
    _validate_snapshot_name(snapshot_name)

    if not source.exists():
        raise ImportError(f"Source file '{source}' does not exist.")
    if not source.is_file():
        raise ImportError(f"Source path '{source}' is not a file.")

    content = _read_env_file(source)
    keys_imported = _count_keys(content)

    if keys_imported == 0:
        raise ImportError(f"No valid KEY=VALUE pairs found in '{source}'.")

    manager.store.save(snapshot_name, content.encode(), password)

    return ImportResult(
        snapshot_name=snapshot_name,
        keys_imported=keys_imported,
        source_path=str(source),
    )
