"""Share snapshots with other users via signed export bundles."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from envpack.store import GitStore, StoreError
from envpack.crypto import encrypt, decrypt


class ShareError(Exception):
    """Raised when a share operation fails."""


@dataclass
class ShareBundle:
    snapshot_name: str
    ciphertext: bytes
    created_at: float
    checksum: str

    def to_dict(self) -> dict:
        return {
            "snapshot_name": self.snapshot_name,
            "ciphertext": self.ciphertext.hex(),
            "created_at": self.created_at,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShareBundle":
        return cls(
            snapshot_name=data["snapshot_name"],
            ciphertext=bytes.fromhex(data["ciphertext"]),
            created_at=data["created_at"],
            checksum=data["checksum"],
        )

    def verify(self) -> bool:
        """Verify the bundle checksum matches its ciphertext."""
        expected = hashlib.sha256(self.ciphertext).hexdigest()
        return self.checksum == expected


def export_bundle(
    store: GitStore,
    snapshot_name: str,
    old_password: str,
    share_password: str,
) -> ShareBundle:
    """Export a snapshot re-encrypted with a share password."""
    try:
        raw = store.load(snapshot_name)
    except StoreError as exc:
        raise ShareError(str(exc)) from exc

    try:
        plaintext = decrypt(raw, old_password)
    except Exception as exc:
        raise ShareError(f"Decryption failed: {exc}") from exc

    ciphertext = encrypt(plaintext, share_password)
    checksum = hashlib.sha256(ciphertext).hexdigest()
    return ShareBundle(
        snapshot_name=snapshot_name,
        ciphertext=ciphertext,
        created_at=time.time(),
        checksum=checksum,
    )


def write_bundle(bundle: ShareBundle, dest: Path) -> None:
    """Write a ShareBundle to a JSON file."""
    dest.write_text(json.dumps(bundle.to_dict(), indent=2))


def read_bundle(src: Path) -> ShareBundle:
    """Read and validate a ShareBundle from a JSON file."""
    try:
        data = json.loads(src.read_text())
    except Exception as exc:
        raise ShareError(f"Cannot read bundle: {exc}") from exc
    bundle = ShareBundle.from_dict(data)
    if not bundle.verify():
        raise ShareError("Bundle checksum mismatch — file may be corrupted.")
    return bundle


def import_bundle(
    store: GitStore,
    bundle: ShareBundle,
    share_password: str,
    store_password: str,
    snapshot_name: str | None = None,
) -> str:
    """Import a bundle into the store re-encrypted with the store password."""
    try:
        plaintext = decrypt(bundle.ciphertext, share_password)
    except Exception as exc:
        raise ShareError(f"Decryption failed: {exc}") from exc

    name = snapshot_name or bundle.snapshot_name
    ciphertext = encrypt(plaintext, store_password)
    store.save(name, ciphertext)
    return name
