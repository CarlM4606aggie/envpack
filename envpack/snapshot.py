"""High-level snapshot operations combining crypto and store."""

from pathlib import Path
from typing import Optional

from envpack.crypto import encrypt, decrypt
from envpack.store import GitStore


class SnapshotManager:
    """Orchestrates encrypting .env files and persisting them to the store."""

    def __init__(self, store: Optional[GitStore] = None) -> None:
        self.store = store or GitStore()

    def push(self, env_file: Path, name: str, password: str) -> None:
        """
        Read *env_file*, encrypt it with *password*, and save it to the
        store under *name*.
        """
        if not env_file.exists():
            raise FileNotFoundError(f".env file not found: {env_file}")
        plaintext = env_file.read_bytes()
        ciphertext = encrypt(plaintext, password)
        self.store.save(name, ciphertext)

    def pull(self, name: str, password: str, dest: Path) -> None:
        """
        Load the snapshot *name* from the store, decrypt it with *password*,
        and write the plaintext to *dest*.
        """
        ciphertext = self.store.load(name)
        plaintext = decrypt(ciphertext, password)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(plaintext)

    def list_snapshots(self) -> list[str]:
        """Return all snapshot names currently in the store."""
        return self.store.list_snapshots()

    def delete(self, name: str) -> None:
        """Delete a snapshot from the store."""
        self.store.delete(name)
