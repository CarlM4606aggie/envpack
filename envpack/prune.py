"""Prune old snapshots from the store, keeping only the N most recent per profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envpack.store import GitStore, StoreError


class PruneError(Exception):
    """Raised when pruning fails."""


@dataclass
class PruneResult:
    kept: List[str]
    removed: List[str]

    def summary(self) -> str:
        if not self.removed:
            return f"Nothing to prune. {len(self.kept)} snapshot(s) retained."
        return (
            f"Pruned {len(self.removed)} snapshot(s), "
            f"{len(self.kept)} retained."
        )


def prune_snapshots(
    store: GitStore,
    profile: str,
    keep: int,
) -> PruneResult:
    """Remove all but the *keep* most-recent snapshots for *profile*.

    Snapshots are expected to be named ``<profile>/<timestamp>.env`` so that
    lexicographic sort is equivalent to chronological order.

    Args:
        store:   Initialised :class:`GitStore` instance.
        profile: Profile name whose snapshots should be pruned.
        keep:    Number of most-recent snapshots to retain (must be >= 1).

    Returns:
        A :class:`PruneResult` describing what was kept and removed.

    Raises:
        PruneError: If *keep* is less than 1 or the store operation fails.
    """
    if keep < 1:
        raise PruneError("'keep' must be at least 1.")

    try:
        all_snapshots: List[str] = store.list_snapshots(profile)
    except StoreError as exc:
        raise PruneError(f"Failed to list snapshots: {exc}") from exc

    # Lexicographic sort — ISO-8601 timestamps sort chronologically.
    sorted_snapshots = sorted(all_snapshots)

    to_keep = sorted_snapshots[-keep:]
    to_remove = sorted_snapshots[:-keep] if len(sorted_snapshots) > keep else []

    for name in to_remove:
        try:
            store.delete(profile, name)
        except StoreError as exc:
            raise PruneError(f"Failed to delete snapshot '{name}': {exc}") from exc

    return PruneResult(kept=to_keep, removed=to_remove)
