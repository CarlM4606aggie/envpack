"""Compare two snapshots side-by-side and report differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpack.store import GitStore, StoreError
from envpack.crypto import decrypt


@dataclass
class CompareError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class KeyDiff:
    key: str
    left_value: Optional[str]   # None means key absent on left
    right_value: Optional[str]  # None means key absent on right

    @property
    def status(self) -> str:
        if self.left_value is None:
            return "added"
        if self.right_value is None:
            return "removed"
        return "changed"

    def __str__(self) -> str:
        if self.status == "added":
            return f"  + {self.key}={self.right_value}"
        if self.status == "removed":
            return f"  - {self.key}={self.left_value}"
        return f"  ~ {self.key}: {self.left_value!r} -> {self.right_value!r}"


@dataclass
class CompareResult:
    left: str
    right: str
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.diffs)

    def summary(self) -> str:
        if not self.has_differences:
            return f"Snapshots '{self.left}' and '{self.right}' are identical."
        added = sum(1 for d in self.diffs if d.status == "added")
        removed = sum(1 for d in self.diffs if d.status == "removed")
        changed = sum(1 for d in self.diffs if d.status == "changed")
        parts = []
        if added:
            parts.append(f"{added} added")
        if removed:
            parts.append(f"{removed} removed")
        if changed:
            parts.append(f"{changed} changed")
        return f"'{self.left}' vs '{self.right}': {', '.join(parts)}"


def _parse_env(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def compare_snapshots(
    store: GitStore,
    left_name: str,
    right_name: str,
    password: str,
) -> CompareResult:
    """Decrypt and compare two named snapshots key-by-key."""
    for name in (left_name, right_name):
        if name not in store.list():
            raise CompareError(f"Snapshot not found: {name}")

    left_env = _parse_env(decrypt(store.load(left_name), password))
    right_env = _parse_env(decrypt(store.load(right_name), password))

    all_keys = sorted(set(left_env) | set(right_env))
    diffs: List[KeyDiff] = []
    for key in all_keys:
        lv = left_env.get(key)
        rv = right_env.get(key)
        if lv != rv:
            diffs.append(KeyDiff(key=key, left_value=lv, right_value=rv))

    return CompareResult(left=left_name, right=right_name, diffs=diffs)
