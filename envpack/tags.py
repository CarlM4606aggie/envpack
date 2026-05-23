"""Tag management for envpack snapshots."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]{1,64}$')


class TagError(Exception):
    """Raised when a tag operation fails."""


@dataclass
class TagIndex:
    """Maps human-readable tags to snapshot identifiers."""

    _path: Path
    _data: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "TagIndex":
        index = cls(_path=path)
        if path.exists():
            import json
            index._data = json.loads(path.read_text())
        return index

    def save(self) -> None:
        import json
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    def set(self, tag: str, snapshot_id: str) -> None:
        _validate_tag(tag)
        self._data[tag] = snapshot_id
        self.save()

    def get(self, tag: str) -> Optional[str]:
        return self._data.get(tag)

    def delete(self, tag: str) -> None:
        if tag not in self._data:
            raise TagError(f"Tag '{tag}' does not exist.")
        del self._data[tag]
        self.save()

    def list_tags(self) -> List[tuple]:
        """Return sorted list of (tag, snapshot_id) pairs."""
        return sorted(self._data.items())


def _validate_tag(tag: str) -> None:
    if not TAG_PATTERN.match(tag):
        raise TagError(
            f"Invalid tag '{tag}'. Tags must be 1-64 characters: "
            "letters, digits, '_', '-', or '.'."
        )
