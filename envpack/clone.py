"""Clone a remote Git-backed store to a local path."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class CloneError(Exception):
    """Raised when cloning a remote store fails."""


@dataclass
class CloneResult:
    source: str
    destination: Path
    snapshot_count: int

    def summary(self) -> str:
        return (
            f"Cloned '{self.source}' → '{self.destination}' "
            f"({self.snapshot_count} snapshot(s) found)"
        )


def clone_store(source: str, destination: Path) -> CloneResult:
    """Clone *source* (a Git remote URL or local path) into *destination*.

    Parameters
    ----------
    source:
        A Git-compatible remote URL or a local filesystem path.
    destination:
        The local directory to clone into.  Must not already exist.

    Raises
    ------
    CloneError
        If the destination already exists or ``git clone`` fails.
    """
    if destination.exists():
        raise CloneError(f"Destination already exists: {destination}")

    try:
        subprocess.run(
            ["git", "clone", source, str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        raise CloneError(f"git clone failed: {stderr}") from exc

    snapshot_count = _count_snapshots(destination)
    return CloneResult(source=source, destination=destination, snapshot_count=snapshot_count)


def _count_snapshots(store_dir: Path) -> int:
    """Return the number of .enc snapshot files present in *store_dir*."""
    return len(list(store_dir.rglob("*.enc")))
