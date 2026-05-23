"""Audit log for tracking snapshot push/pull operations."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


AUDIT_FILENAME = "audit.log"


@dataclass
class AuditEntry:
    action: str          # "push" or "pull"
    profile: str
    snapshot_name: str
    env_path: str
    timestamp: str
    note: Optional[str] = None

    @staticmethod
    def now(action: str, profile: str, snapshot_name: str, env_path: str, note: Optional[str] = None) -> "AuditEntry":
        return AuditEntry(
            action=action,
            profile=profile,
            snapshot_name=snapshot_name,
            env_path=str(env_path),
            timestamp=datetime.now(timezone.utc).isoformat(),
            note=note,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(line: str) -> "AuditEntry":
        data = json.loads(line)
        return AuditEntry(**data)


class AuditLog:
    def __init__(self, store_path: Path) -> None:
        self._path = store_path / AUDIT_FILENAME

    def record(self, entry: AuditEntry) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json() + "\n")

    def entries(self, limit: Optional[int] = None) -> List[AuditEntry]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as fh:
            lines = [l.strip() for l in fh if l.strip()]
        parsed = [AuditEntry.from_json(l) for l in lines]
        parsed.reverse()
        return parsed[:limit] if limit is not None else parsed

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
