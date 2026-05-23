"""Snapshot integrity verification for envpack."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List

from envpack.store import GitStore, StoreError
from envpack.crypto import decrypt


class VerifyError(Exception):
    """Raised when verification cannot be performed."""


@dataclass
class VerifyResult:
    snapshot: str
    ok: bool
    error: str = ""

    def __str__(self) -> str:
        status = "OK" if self.ok else f"FAIL ({self.error})"
        return f"{self.snapshot}: {status}"


@dataclass
class VerifyReport:
    results: List[VerifyResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def failed(self) -> List[VerifyResult]:
        return [r for r in self.results if not r.ok]

    def summary(self) -> str:
        total = len(self.results)
        bad = len(self.failed)
        if total == 0:
            return "No snapshots found."
        if bad == 0:
            return f"All {total} snapshot(s) verified successfully."
        return f"{bad}/{total} snapshot(s) failed verification."


def verify_snapshots(store: GitStore, password: str, profile: str = "default") -> VerifyReport:
    """Attempt to decrypt every snapshot for *profile* and report results."""
    try:
        names = store.list(profile)
    except StoreError as exc:
        raise VerifyError(str(exc)) from exc

    report = VerifyReport()
    for name in names:
        try:
            ciphertext = store.load(profile, name)
            plaintext = decrypt(ciphertext, password)
            # Basic sanity: result must be decodable UTF-8
            plaintext.decode("utf-8")
            result = VerifyResult(snapshot=name, ok=True)
        except Exception as exc:  # noqa: BLE001
            result = VerifyResult(snapshot=name, ok=False, error=str(exc))
        report.results.append(result)

    return report
