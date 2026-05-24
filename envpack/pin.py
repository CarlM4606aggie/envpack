"""Snapshot pinning — mark snapshots so they are protected from prune/rotate."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

PIN_FILE = "pins.json"


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class PinIndex:
    _store_dir: Path
    _pins: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    def load(self) -> "PinIndex":
        path = self._store_dir / PIN_FILE
        if path.exists():
            data = json.loads(path.read_text())
            self._pins = data.get("pins", [])
        return self

    def save(self) -> None:
        path = self._store_dir / PIN_FILE
        path.write_text(json.dumps({"pins": self._pins}, indent=2))

    # ------------------------------------------------------------------
    def pin(self, name: str) -> None:
        """Mark *name* as pinned."""
        if not name:
            raise PinError("Snapshot name must not be empty.")
        if name not in self._pins:
            self._pins.append(name)
            self.save()

    def unpin(self, name: str) -> None:
        """Remove pin from *name*.  No-op if not pinned."""
        if name in self._pins:
            self._pins.remove(name)
            self.save()

    def is_pinned(self, name: str) -> bool:
        return name in self._pins

    def list_pins(self) -> List[str]:
        return list(self._pins)


def load_index(store_dir: Path) -> PinIndex:
    """Convenience: create and load a PinIndex from *store_dir*."""
    return PinIndex(_store_dir=store_dir).load()
