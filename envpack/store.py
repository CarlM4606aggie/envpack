"""Git-backed store for managing encrypted .env snapshots."""

import os
import subprocessrom pathlib import Path
from typing import Optional


DEFAULT_STORE_DIR = Path.home() / ".envpack" / "store"


class StoreError(Exception):
    """Raised when a store operation fails."""


class GitStore:
    """Manages a local Git repository used as the encrypted env store."""

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR

    def init(self) -> None:
        """Initialize the store directory and Git repository."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        if not (self.store_dir / ".git").exists():
            self._run_git("init")
            self._run_git("commit", "--allow-empty", "-m", "init envpack store")

    def save(self, name: str, data: bytes) -> None:
        """Write encrypted data to a named file and commit it."""
        self._ensure_initialized()
        target = self.store_dir / f"{name}.enc"
        target.write_bytes(data)
        self._run_git("add", str(target))
        self._run_git("commit", "-m", f"snapshot: {name}")

    def load(self, name: str) -> bytes:
        """Read encrypted data for the given snapshot name."""
        self._ensure_initialized()
        target = self.store_dir / f"{name}.enc"
        if not target.exists():
            raise StoreError(f"Snapshot '{name}' not found in store.")
        return target.read_bytes()

    def list_snapshots(self) -> list[str]:
        """Return names of all stored snapshots."""
        self._ensure_initialized()
        return [
            p.stem
            for p in sorted(self.store_dir.glob("*.enc"))
        ]

    def delete(self, name: str) -> None:
        """Remove a snapshot from the store and commit the deletion."""
        self._ensure_initialized()
        target = self.store_dir / f"{name}.enc"
        if not target.exists():
            raise StoreError(f"Snapshot '{name}' not found in store.")
        self._run_git("rm", str(target))
        self._run_git("commit", "-m", f"delete: {name}")

    def _ensure_initialized(self) -> None:
        if not (self.store_dir / ".git").exists():
            raise StoreError(
                f"Store not initialized. Run `envpack init` first."
            )

    def _run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.store_dir), *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise StoreError(
                f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}"
            )
        return result.stdout.strip()
