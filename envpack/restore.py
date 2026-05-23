"""Restore a snapshot to a target path with optional backup of existing file."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from envpack.store import GitStore, StoreError
from envpack.crypto import decrypt


class RestoreError(Exception):
    """Raised when a restore operation fails."""


@dataclass
class RestoreResult:
    snapshot_name: str
    target: Path
    backup_path: Path | None
    overwrote_existing: bool

    def summary(self) -> str:
        parts = [f"Restored '{self.snapshot_name}' -> {self.target}"]
        if self.backup_path:
            parts.append(f"Existing file backed up to {self.backup_path}")
        return "\n".join(parts)


def restore_snapshot(
    store: GitStore,
    snapshot_name: str,
    password: str,
    target: Path,
    *,
    backup: bool = True,
) -> RestoreResult:
    """Decrypt a snapshot and write it to *target*.

    If *backup* is True and *target* already exists, a timestamped backup is
    created alongside the target before overwriting.
    """
    try:
        ciphertext = store.load(snapshot_name)
    except StoreError as exc:
        raise RestoreError(f"Snapshot not found: {snapshot_name}") from exc

    try:
        plaintext = decrypt(ciphertext, password)
    except Exception as exc:
        raise RestoreError("Decryption failed — wrong password?") from exc

    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    overwrote = target.exists()

    if overwrote and backup:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        backup_path = target.with_suffix(f".{timestamp}.bak")
        shutil.copy2(target, backup_path)

    target.write_bytes(plaintext)

    return RestoreResult(
        snapshot_name=snapshot_name,
        target=target,
        backup_path=backup_path,
        overwrote_existing=overwrote,
    )
