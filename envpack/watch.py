"""Watch a .env file for changes and auto-push snapshots."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    path: Path
    old_hash: Optional[str]
    new_hash: str
    timestamp: float = field(default_factory=time.time)

    @property
    def is_first_seen(self) -> bool:
        return self.old_hash is None


def _file_hash(path: Path) -> Optional[str]:
    """Return SHA-256 hex digest of *path*, or None if the file is missing."""
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except FileNotFoundError:
        return None


def watch_file(
    path: Path,
    on_change: Callable[[WatchEvent], None],
    *,
    interval: float = 2.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds and call *on_change* when it changes.

    Parameters
    ----------
    path:           File to monitor.
    on_change:      Callback invoked with a :class:`WatchEvent` on each change.
    interval:       Polling interval in seconds.
    max_iterations: Stop after this many iterations (useful for testing).
    """
    if not path.parent.exists():
        raise WatchError(f"Directory does not exist: {path.parent}")

    current_hash: Optional[str] = _file_hash(path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        new_hash = _file_hash(path)
        if new_hash != current_hash:
            event = WatchEvent(path=path, old_hash=current_hash, new_hash=new_hash or "")
            on_change(event)
            current_hash = new_hash
        iterations += 1
