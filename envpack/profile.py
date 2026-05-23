"""Profile management for envpack — handles named environment profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ProfileError(Exception):
    """Raised when a profile operation fails."""


@dataclass
class Profile:
    """Represents a named environment profile."""

    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name or not self.name.isidentifier():
            raise ProfileError(
                f"Profile name {self.name!r} must be a valid identifier."
            )

    def matches_tag(self, tag: str) -> bool:
        """Return True if this profile has the given tag."""
        return tag in self.tags


class ProfileManager:
    """Manages profiles stored within the Git-backed store directory."""

    _PROFILES_FILE = "profiles.json"

    def __init__(self, store_path: Path) -> None:
        self._store_path = Path(store_path)
        self._profiles_file = self._store_path / self._PROFILES_FILE

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_all(self) -> dict:
        import json

        if not self._profiles_file.exists():
            return {}
        with self._profiles_file.open() as fh:
            return json.load(fh)

    def _save_all(self, data: dict) -> None:
        import json

        self._store_path.mkdir(parents=True, exist_ok=True)
        with self._profiles_file.open("w") as fh:
            json.dump(data, fh, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, profile: Profile) -> None:
        """Persist a new profile; raise ProfileError if it already exists."""
        data = self._load_all()
        if profile.name in data:
            raise ProfileError(f"Profile {profile.name!r} already exists.")
        data[profile.name] = {"description": profile.description, "tags": profile.tags}
        self._save_all(data)

    def get(self, name: str) -> Profile:
        """Return a Profile by name; raise ProfileError if not found."""
        data = self._load_all()
        if name not in data:
            raise ProfileError(f"Profile {name!r} not found.")
        entry = data[name]
        return Profile(name=name, description=entry.get("description", ""), tags=entry.get("tags", []))

    def list_profiles(self) -> List[Profile]:
        """Return all stored profiles."""
        data = self._load_all()
        return [
            Profile(name=k, description=v.get("description", ""), tags=v.get("tags", []))
            for k, v in data.items()
        ]

    def delete(self, name: str) -> None:
        """Remove a profile; raise ProfileError if not found."""
        data = self._load_all()
        if name not in data:
            raise ProfileError(f"Profile {name!r} not found.")
        del data[name]
        self._save_all(data)

    def exists(self, name: str) -> bool:
        """Return True if a profile with *name* exists."""
        return name in self._load_all()
