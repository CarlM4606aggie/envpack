"""Utilities for diffing .env file snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvDiff:
    """Represents the diff between two .env snapshots."""

    added: Dict[str, str]
    removed: Dict[str, str]
    changed: Dict[str, Tuple[str, str]]  # key -> (old_value, new_value)
    unchanged: Dict[str, str]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines: List[str] = []
        for key, value in sorted(self.added.items()):
            lines.append(f"+ {key}={value}")
        for key, value in sorted(self.removed.items()):
            lines.append(f"- {key}={value}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "(no changes)"


def _parse_env(text: str) -> Dict[str, str]:
    """Parse .env file text into a key/value dict, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def diff_env_texts(old_text: Optional[str], new_text: Optional[str]) -> EnvDiff:
    """Compute the diff between two .env file strings.

    Pass ``None`` to represent a missing/empty file.
    """
    old = _parse_env(old_text or "")
    new = _parse_env(new_text or "")

    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    changed = {
        k: (old[k], new[k])
        for k in old.keys() & new.keys()
        if old[k] != new[k]
    }
    unchanged = {
        k: v for k, v in old.items() if k in new and old[k] == new[k]
    }
    return EnvDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
