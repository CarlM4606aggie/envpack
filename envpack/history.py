"""Snapshot history browsing and summary for envpack."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envpack.store import GitStore, StoreError


class HistoryError(Exception):
    """Raised when history operations fail."""


@dataclass
class HistoryEntry:
    name: str
    index: int  # 0 = most recent
    size_bytes: int

    def __str__(self) -> str:
        return f"[{self.index}] {self.name} ({self.size_bytes} bytes)"


@dataclass
class HistoryReport:
    entries: List[HistoryEntry]

    @property
    def total(self) -> int:
        return len(self.entries)

    def summary(self) -> str:
        if not self.entries:
            return "No snapshots found."
        lines = [f"{self.total} snapshot(s):"] + [str(e) for e in self.entries]
        return "\n".join(lines)


def get_history(
    store: GitStore,
    limit: Optional[int] = None,
) -> HistoryReport:
    """Return an ordered history report for all snapshots in *store*.

    Snapshots are listed newest-first (alphabetical descending by name).
    """
    try:
        names = store.list()
    except StoreError as exc:
        raise HistoryError(f"Could not list snapshots: {exc}") from exc

    names_sorted = sorted(names, reverse=True)
    if limit is not None:
        names_sorted = names_sorted[:limit]

    entries: List[HistoryEntry] = []
    for idx, name in enumerate(names_sorted):
        try:
            data = store.load(name)
        except StoreError:
            size = 0
        else:
            size = len(data)
        entries.append(HistoryEntry(name=name, index=idx, size_bytes=size))

    return HistoryReport(entries=entries)
