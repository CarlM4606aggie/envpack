"""Merge two .env snapshots or files, resolving key conflicts.

Supports three strategies:
  - ours:   keep values from the base snapshot on conflict
  - theirs: keep values from the incoming snapshot on conflict
  - prompt: (used by CLI) raise MergeConflict listing keys that need resolution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class MergeStrategy(str, Enum):
    OURS = "ours"
    THEIRS = "theirs"
    PROMPT = "prompt"


class MergeError(Exception):
    """Raised when a merge cannot be completed automatically."""


@dataclass
class MergeConflict:
    """Describes a single key that differs between base and incoming."""

    key: str
    base_value: Optional[str]
    incoming_value: Optional[str]

    def __str__(self) -> str:
        return (
            f"{self.key}: base={self.base_value!r} "
            f"vs incoming={self.incoming_value!r}"
        )


@dataclass
class MergeResult:
    """Outcome of a merge operation."""

    merged: Dict[str, str]
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    conflicts_resolved: List[MergeConflict] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.updated:
            parts.append(f"~{len(self.updated)} updated")
        if self.conflicts_resolved:
            parts.append(f"{len(self.conflicts_resolved)} conflict(s) resolved")
        return ", ".join(parts) if parts else "no changes"


def _parse_env(text: str) -> Dict[str, str]:
    """Parse .env text into a key→value mapping, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def _render_env(mapping: Dict[str, str]) -> str:
    """Serialize a key→value mapping back to .env text."""
    return "\n".join(f"{k}={v}" for k, v in mapping.items()) + "\n"


def merge_env_texts(
    base: str,
    incoming: str,
    strategy: MergeStrategy = MergeStrategy.OURS,
) -> MergeResult:
    """Merge two .env texts according to *strategy*.

    Args:
        base:     The existing/local .env content.
        incoming: The new/remote .env content to merge in.
        strategy: How to resolve conflicting keys.

    Returns:
        A :class:`MergeResult` whose ``merged`` dict contains the final state.

    Raises:
        MergeError: When *strategy* is ``PROMPT`` and conflicts exist.
    """
    base_map = _parse_env(base)
    inc_map = _parse_env(incoming)

    all_keys = set(base_map) | set(inc_map)
    merged: Dict[str, str] = {}
    added: List[str] = []
    removed: List[str] = []
    updated: List[str] = []
    conflicts: List[MergeConflict] = []

    for key in sorted(all_keys):
        in_base = key in base_map
        in_inc = key in inc_map

        if in_base and not in_inc:
            # Key was removed in incoming — drop it.
            removed.append(key)
        elif in_inc and not in_base:
            # New key introduced by incoming — always add.
            merged[key] = inc_map[key]
            added.append(key)
        else:
            # Present in both — check for conflict.
            if base_map[key] == inc_map[key]:
                merged[key] = base_map[key]
            else:
                conflict = MergeConflict(
                    key=key,
                    base_value=base_map[key],
                    incoming_value=inc_map[key],
                )
                if strategy == MergeStrategy.OURS:
                    merged[key] = base_map[key]
                    conflicts.append(conflict)
                elif strategy == MergeStrategy.THEIRS:
                    merged[key] = inc_map[key]
                    conflicts.append(conflict)
                else:  # PROMPT
                    conflicts.append(conflict)
                updated.append(key)

    if strategy == MergeStrategy.PROMPT and conflicts:
        conflict_lines = "\n  ".join(str(c) for c in conflicts)
        raise MergeError(
            f"Merge conflicts require manual resolution:\n  {conflict_lines}"
        )

    return MergeResult(
        merged=merged,
        added=added,
        removed=removed,
        updated=updated,
        conflicts_resolved=conflicts,
    )
