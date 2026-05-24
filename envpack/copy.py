"""Copy a snapshot from one name to another within the store."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envpack.store import GitStore, StoreError


class CopyError(Exception):
    """Raised when a snapshot copy operation fails."""


@dataclass
class CopyResult:
    source: str
    destination: str
    profile: str

    def summary(self) -> str:
        return (
            f"Copied '{self.source}' -> '{self.destination}' "
            f"(profile: {self.profile})"
        )


def copy_snapshot(
    store: GitStore,
    source: str,
    destination: str,
    profile: str = "default",
    password: Optional[str] = None,
) -> CopyResult:
    """Copy an existing snapshot to a new name.

    The raw encrypted bytes are duplicated verbatim — no re-encryption is
    performed, so the same password continues to work for both entries.
    """
    try:
        raw = store.load(source, profile)
    except StoreError as exc:
        raise CopyError(f"Source snapshot not found: {source!r}") from exc

    existing = store.list(profile)
    if destination in existing:
        raise CopyError(
            f"Destination snapshot already exists: {destination!r}. "
            "Use --force or choose a different name."
        )

    store.save(destination, profile, raw)
    return CopyResult(source=source, destination=destination, profile=profile)
