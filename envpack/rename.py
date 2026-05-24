"""Rename a snapshot key (label) within the store."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from envpack.store import GitStore, StoreError


class RenameError(Exception):
    """Raised when a rename operation fails."""


@dataclass
class RenameResult:
    old_name: str
    new_name: str
    store_path: Path

    def summary(self) -> str:
        return (
            f"Renamed snapshot '{self.old_name}' -> '{self.new_name}' "
            f"in store '{self.store_path}'."
        )


def rename_snapshot(
    store: GitStore,
    old_name: str,
    new_name: str,
    password: str,
) -> RenameResult:
    """Rename *old_name* to *new_name* inside *store*.

    The encrypted blob is loaded under the old name, saved under the new name,
    and the old entry is deleted.  A git commit is made for the operation.

    Raises
    ------
    RenameError
        If *old_name* does not exist, *new_name* already exists, or the names
        are identical.
    """
    if old_name == new_name:
        raise RenameError("Old and new names are identical.")

    snapshots = store.list()
    if old_name not in snapshots:
        raise RenameError(f"Snapshot '{old_name}' not found.")
    if new_name in snapshots:
        raise RenameError(f"Snapshot '{new_name}' already exists.")

    try:
        raw: bytes = store.load(old_name)
    except StoreError as exc:
        raise RenameError(str(exc)) from exc

    try:
        store.save(new_name, raw)
        store.delete(old_name)
    except StoreError as exc:
        raise RenameError(str(exc)) from exc

    return RenameResult(
        old_name=old_name,
        new_name=new_name,
        store_path=Path(store.path),
    )
