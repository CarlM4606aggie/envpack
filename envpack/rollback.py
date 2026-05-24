"""Rollback support: revert a target file to a previous snapshot version."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envpack.store import GitStore, StoreError
from envpack.crypto import decrypt


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


@dataclass
class RollbackResult:
    snapshot_name: str
    target: Path
    backup: Optional[Path]

    def summary(self) -> str:
        parts = [f"Rolled back '{self.target}' from snapshot '{self.snapshot_name}'."]
        if self.backup:
            parts.append(f"Previous file backed up to '{self.backup}'.")
        return " ".join(parts)


def rollback_snapshot(
    store: GitStore,
    snapshot_name: str,
    password: str,
    target: Path,
    backup: bool = True,
) -> RollbackResult:
    """Decrypt *snapshot_name* and overwrite *target* with its contents.

    If *backup* is True and *target* already exists, the existing file is
    renamed to ``<target>.bak`` before being overwritten.

    Raises
    ------
    RollbackError
        If the snapshot cannot be found or decryption fails.
    """
    try:
        ciphertext = store.load(snapshot_name)
    except StoreError as exc:
        raise RollbackError(str(exc)) from exc

    try:
        plaintext = decrypt(ciphertext, password)
    except Exception as exc:
        raise RollbackError(f"Decryption failed: {exc}") from exc

    backup_path: Optional[Path] = None
    if backup and target.exists():
        backup_path = target.with_suffix(target.suffix + ".bak")
        target.rename(backup_path)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(plaintext)

    return RollbackResult(
        snapshot_name=snapshot_name,
        target=target,
        backup=backup_path,
    )
