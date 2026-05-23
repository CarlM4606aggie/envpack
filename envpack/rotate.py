"""Password rotation: re-encrypt all snapshots with a new password."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from envpack.crypto import decrypt, encrypt
from envpack.store import GitStore, StoreError


class RotateError(Exception):
    """Raised when rotation fails."""


@dataclass
class RotationResult:
    rotated: List[str]
    failed: List[str]

    @property
    def success(self) -> bool:
        return len(self.failed) == 0

    def summary(self) -> str:
        lines = [f"Rotated: {len(self.rotated)}  Failed: {len(self.failed)}"]
        for name in self.rotated:
            lines.append(f"  ✓ {name}")
        for name in self.failed:
            lines.append(f"  ✗ {name}")
        return "\n".join(lines)


def rotate_snapshots(
    store: GitStore,
    old_password: str,
    new_password: str,
    profile: str = "default",
) -> RotationResult:
    """Re-encrypt every snapshot for *profile* with *new_password*."""
    try:
        names = store.list(profile)
    except StoreError as exc:
        raise RotateError(f"Cannot list snapshots: {exc}") from exc

    rotated: List[str] = []
    failed: List[str] = []

    for name in names:
        try:
            ciphertext = store.load(profile, name)
            plaintext = decrypt(ciphertext, old_password)
            new_ciphertext = encrypt(plaintext, new_password)
            store.save(profile, name, new_ciphertext, message=f"rotate: {profile}/{name}")
            rotated.append(name)
        except Exception:  # noqa: BLE001
            failed.append(name)

    return RotationResult(rotated=rotated, failed=failed)
