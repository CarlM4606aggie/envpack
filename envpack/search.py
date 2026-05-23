"""Search snapshots by key presence or value patterns."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional

from envpack.store import GitStore
from envpack.crypto import decrypt


@dataclass
class SearchMatch:
    snapshot: str
    key: str
    value: str

    def __str__(self) -> str:
        return f"{self.snapshot}: {self.key}={self.value}"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    def summary(self) -> str:
        if not self.has_matches:
            return "No matches found."
        lines = [str(m) for m in self.matches]
        return "\n".join(lines)


def _parse_env(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def search_snapshots(
    store: GitStore,
    password: str,
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    snapshot_glob: Optional[str] = None,
) -> SearchResult:
    """Search all snapshots for keys/values matching the given patterns."""
    result = SearchResult()
    snapshots = store.list()

    for snapshot_name in snapshots:
        if snapshot_glob and not fnmatch.fnmatch(snapshot_name, snapshot_glob):
            continue
        try:
            ciphertext = store.load(snapshot_name)
            plaintext = decrypt(ciphertext, password).decode()
        except Exception:
            continue

        env = _parse_env(plaintext)
        for key, value in env.items():
            key_ok = (
                key_pattern is None
                or fnmatch.fnmatch(key, key_pattern)
                or re.search(key_pattern, key) is not None
            )
            value_ok = (
                value_pattern is None
                or fnmatch.fnmatch(value, value_pattern)
                or re.search(value_pattern, value) is not None
            )
            if key_ok and value_ok:
                result.matches.append(SearchMatch(snapshot_name, key, value))

    return result
