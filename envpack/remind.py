"""Snapshot staleness reminders — warn when a snapshot hasn't been updated recently."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from envpack.store import GitStore


class RemindError(Exception):
    """Raised when reminder processing fails."""


@dataclass
class ReminderEntry:
    name: str
    last_modified: datetime
    age_days: float
    threshold_days: int

    def __str__(self) -> str:
        return (
            f"{self.name}: last updated {self.age_days:.1f} days ago "
            f"(threshold: {self.threshold_days}d)"
        )


@dataclass
class ReminderReport:
    entries: List[ReminderEntry]
    threshold_days: int

    @property
    def stale(self) -> List[ReminderEntry]:
        return [e for e in self.entries if e.age_days >= e.threshold_days]

    @property
    def ok(self) -> List[ReminderEntry]:
        return [e for e in self.entries if e.age_days < e.threshold_days]

    def summary(self) -> str:
        if not self.entries:
            return "No snapshots found."
        stale = self.stale
        if not stale:
            return f"All {len(self.entries)} snapshot(s) are up to date."
        lines = [f"{len(stale)} stale snapshot(s) (threshold: {self.threshold_days}d):"]
        lines.extend(f"  - {e}" for e in stale)
        return "\n".join(lines)


def check_staleness(store: GitStore, threshold_days: int = 30) -> ReminderReport:
    """Return a report of snapshots that haven't been updated within *threshold_days*."""
    if threshold_days < 1:
        raise RemindError("threshold_days must be at least 1")

    names = store.list()
    now = datetime.now(tz=timezone.utc)
    entries: List[ReminderEntry] = []

    for name in names:
        mtime = store.last_modified(name)
        if mtime is None:
            continue
        age = (now - mtime).total_seconds() / 86400
        entries.append(
            ReminderEntry(
                name=name,
                last_modified=mtime,
                age_days=round(age, 2),
                threshold_days=threshold_days,
            )
        )

    entries.sort(key=lambda e: e.age_days, reverse=True)
    return ReminderReport(entries=entries, threshold_days=threshold_days)
